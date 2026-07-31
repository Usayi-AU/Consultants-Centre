from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand

from reports.models import SharePointTrackerEntry


class Command(BaseCommand):
    help = "Import the Q1 2026 SharePoint tracker workbook into the dashboard tracker model"

    def import_from_workbook(self, workbook_path):
        workbook_path = Path(workbook_path)
        if not workbook_path.exists():
            self.stdout.write(self.style.WARNING(f"Workbook not found: {workbook_path}"))
            return

        workbook = openpyxl.load_workbook(workbook_path, data_only=True)
        sheet = workbook["1Q26"]

        imported = 0
        for row in sheet.iter_rows(min_row=3, values_only=True):
            if not row or not row[0]:
                continue
            client_name = str(row[0]).strip() if row[0] is not None else ""
            if not client_name or client_name.lower().startswith("client name"):
                continue
            crm_name = str(row[1]).strip() if row[1] is not None else ""
            alternate_name = str(row[2]).strip() if row[2] is not None else ""

            def _is_marked(value):
                if isinstance(value, bool):
                    return value
                if value is None:
                    return False
                if isinstance(value, (int, float)):
                    return bool(value)
                return str(value).strip() in {"✓", "✔", "X", "x", "Y", "y", "TRUE", "True", "true", "1"}

            word_submitted = _is_marked(row[3]) if len(row) > 3 else False
            excel_submitted = _is_marked(row[4]) if len(row) > 4 else False
            pdf_submitted = _is_marked(row[5]) if len(row) > 5 else False
            due_date = str(row[6]).strip() if len(row) > 6 and row[6] is not None else ""
            notes = ""

            entry, created = SharePointTrackerEntry.objects.get_or_create(
                quarter="q1",
                client_name=client_name,
                defaults={
                    "quarter": "q1",
                    "crm_name": crm_name,
                    "alternate_name": alternate_name,
                    "word_submitted": word_submitted,
                    "excel_submitted": excel_submitted,
                    "pdf_submitted": pdf_submitted,
                    "due_date": due_date,
                    "notes": notes,
                },
            )
            if not created:
                entry.crm_name = crm_name
                entry.alternate_name = alternate_name
                entry.word_submitted = word_submitted
                entry.excel_submitted = excel_submitted
                entry.pdf_submitted = pdf_submitted
                entry.due_date = due_date
                entry.notes = notes
                entry.save()
            imported += 1
            self.stdout.write(self.style.SUCCESS(f"Imported {client_name}"))

        return imported

    def handle(self, *args, **options):
        workbook_path = Path(__file__).resolve().parents[3] / "Q12026 SHarepoint Tracker.xlsx"
        return self.import_from_workbook(workbook_path)
