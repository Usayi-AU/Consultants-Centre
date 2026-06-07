from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from reports.models import AlternativeInvestmentItem
from reports.utils import (
    alt_headline_color_for_text,
    alt_name_key,
    default_static_workbook,
    export_alt_document_content,
    load_alt_investment_detail_sections,
    parse_alt_investments_from_docx,
)


class Command(BaseCommand):
    help = "Import Alternative Investments dashboard data from the Word update document."

    def add_arguments(self, parser):
        parser.add_argument(
            "--document",
            type=str,
            default=None,
            help="Path to Alternative Investments .docx (defaults to latest file in static/).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing alternative investment records before importing.",
        )

    def handle(self, *args, **options):
        document_path = options["document"]
        if document_path:
            source_path = Path(document_path)
            if not source_path.is_absolute():
                source_path = Path(settings.BASE_DIR) / source_path
        else:
            source_path = default_static_workbook("Alternative Investments*.docx")
            if not source_path:
                raise CommandError("No Alternative Investments .docx found in static/.")

        if not source_path.exists():
            raise CommandError(f"Document not found: {source_path}")

        export_alt_document_content(source_path)
        load_alt_investment_detail_sections.cache_clear()
        entries, detail_sections = parse_alt_investments_from_docx(source_path)

        if options["reset"]:
            deleted_count, _ = AlternativeInvestmentItem.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing alternative investment records."))

        created = 0
        updated = 0
        for entry in entries:
            section = detail_sections.get(alt_name_key(entry["investment_name"]), {})
            status_headline = entry.get("status_headline") or entry.get("summary_update", "")
            entry_defaults = {
                **entry,
                "status_headline": status_headline,
                "status_headline_color": alt_headline_color_for_text(status_headline, entry.get("status")),
                "risk": section.get("risk", entry.get("risk", "")),
                "investment_details": "\n".join(section.get("investment_details", [])),
                "pension_funds_invested": "\n".join(section.get("pension_funds_invested", [])),
                "status_developments": "\n".join(section.get("status_developments", [])),
                "performance": "\n".join(section.get("performance", [])),
            }
            _, is_created = AlternativeInvestmentItem.objects.update_or_create(
                investment_name=entry["investment_name"],
                defaults=entry_defaults,
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported alternative investments from {source_path.name} (created={created}, updated={updated})."
            )
        )
