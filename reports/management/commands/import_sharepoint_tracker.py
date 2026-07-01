import os
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand

from reports.models import SharePointTrackerEntry


class Command(BaseCommand):
    help = "Import the Q1 2026 SharePoint tracker workbook into the dashboard tracker model"

    def handle(self, *args, **options):
        workbook_path = Path(__file__).resolve().parents[3] / "Q12026 SHarepoint Tracker.xlsx"
        if not workbook_path.exists():
            self.stdout.write(self.style.WARNING(f"Workbook not found: {workbook_path}"))
            return

        workbook = openpyxl.load_workbook(workbook_path, data_only=True)
        sheet = workbook["1Q26"]

        for row in sheet.iter_rows(min_row=4, values_only=True):
            if not row or not row[0]:
                continue
            client_name = str(row[0]).strip() if row[0] is not None else ""
            if not client_name or client_name.lower().startswith("client name"):
                continue
            crm_name = str(row[1]).strip() if row[1] is not None else ""
            alternate_name = str(row[2]).strip() if row[2] is not None else ""
            word_submitted = str(row[3]).strip() == "✓"
            excel_submitted = str(row[4]).strip() == "✓"
            pdf_submitted = str(row[5]).strip() == "✓"
            due_date = str(row[6]).strip() if row[6] is not None else ""
            notes = ""
            if client_name and not SharePointTrackerEntry.objects.filter(client_name=client_name).exists():
                SharePointTrackerEntry.objects.create(
                    client_name=client_name,
                    crm_name=crm_name,
                    alternate_name=alternate_name,
                    word_submitted=word_submitted,
                    excel_submitted=excel_submitted,
                    pdf_submitted=pdf_submitted,
                    due_date=due_date,
                    notes=notes,
                )
                self.stdout.write(self.style.SUCCESS(f"Imported {client_name}"))
