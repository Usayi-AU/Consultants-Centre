from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from reports.utils import default_static_workbook


class Command(BaseCommand):
    help = "Import all dashboard workbooks from the static folder."

    def add_arguments(self, parser):
        parser.add_argument("--operations-workbook", type=str, default=None)
        parser.add_argument("--crm-workbook", type=str, default=None)
        parser.add_argument("--bd-workbook", type=str, default=None)
        parser.add_argument("--alt-document", type=str, default=None)

    def resolve_path(self, explicit_path, pattern, label):
        if explicit_path:
            path = Path(explicit_path)
            if not path.is_absolute():
                path = Path(settings.BASE_DIR) / path
        else:
            path = default_static_workbook(pattern)
            if not path:
                raise CommandError(f"No {label} file found in static/ matching {pattern}")
        if not path.exists():
            raise CommandError(f"{label} file not found: {path}")
        return path

    def handle(self, *args, **options):
        operations_path = self.resolve_path(
            options["operations_workbook"],
            "Q1*Report Tracker*.xlsx",
            "Operations tracker",
        )
        crm_path = self.resolve_path(
            options["crm_workbook"],
            "Action_Items_Dashboard*.xlsx",
            "Client Relations action items",
        )
        bd_path = self.resolve_path(
            options["bd_workbook"],
            "Intellego_IPS_Business_Development_Tracker.xlsx",
            "Business Development tracker",
        )
        alt_path = self.resolve_path(
            options["alt_document"],
            "Alternative Investments*.docx",
            "Alternative Investments update",
        )

        self.stdout.write(self.style.MIGRATE_HEADING("Importing Operations tracker"))
        call_command("import_tracker", workbook=str(operations_path))

        self.stdout.write(self.style.MIGRATE_HEADING("Importing Client Relations action items"))
        call_command("import_excel", path=str(crm_path))

        self.stdout.write(self.style.MIGRATE_HEADING("Importing Business Development tracker"))
        call_command("import_bd_excel", str(bd_path))

        self.stdout.write(self.style.MIGRATE_HEADING("Importing Alternative Investments update"))
        call_command("import_alt_investments", document=str(alt_path), reset=True)

        self.stdout.write(self.style.SUCCESS("All dashboard imports completed."))
