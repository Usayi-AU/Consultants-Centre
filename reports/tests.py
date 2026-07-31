from pathlib import Path
from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from .management.commands.import_sharepoint_tracker import Command as ImportSharePointTrackerCommand
from .models import ClientReport, Proposal, SharePointTrackerEntry, StatusPhase
from .permissions import ADMIN_ACCESS_KEY, ALT_ADMIN_ACCESS_KEY, TEAM_ACCESS_KEY


class ProposalTests(TestCase):
    def test_proposal_add_saves_without_created_by_for_anonymous_request(self):
        session = self.client.session
        session["alt_access_key"] = ALT_ADMIN_ACCESS_KEY
        session["alt_access_level"] = "admin"
        session.save()

        response = self.client.post(
            reverse("proposal_add"),
            {
                "date": "2026-01-12",
                "proposal_name": "Anonymous proposal",
                "status": "received",
                "description": "Created from a session-based admin flow without a logged-in user.",
            },
        )

        self.assertEqual(response.status_code, 302)
        proposal = Proposal.objects.get(proposal_name="Anonymous proposal")
        self.assertIsNone(proposal.created_by)

    def test_status_badge_class_is_styled_for_pending(self):
        proposal = Proposal.objects.create(
            proposal_name="Sample proposal",
            date="2026-01-12",
            status="preliminary",
        )

        self.assertEqual(proposal.status_badge_class, "bg-amber-100 text-amber-800 ring-amber-200")


class DashboardTemplateTests(TestCase):
    def test_sharepoint_tracker_shows_entries_for_team_second_quarter(self):
        SharePointTrackerEntry.objects.create(
            client_name="Client A",
            crm_name="CRM 1",
            alternate_name="Alt 1",
            word_submitted=True,
            excel_submitted=True,
            pdf_submitted=True,
        )

        session = self.client.session
        session["access_key"] = TEAM_ACCESS_KEY
        session["access_level"] = "team"
        session["operations_dashboard_quarter"] = "q2"
        session.save()

        response = self.client.get(reverse("sharepoint_tracker"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["entries"]), 1)

    def test_sharepoint_tracker_shows_entries_for_admin_second_quarter(self):
        SharePointTrackerEntry.objects.create(
            client_name="Client A",
            crm_name="CRM 1",
            alternate_name="Alt 1",
            word_submitted=True,
            excel_submitted=False,
            pdf_submitted=False,
        )

        session = self.client.session
        session["access_key"] = ADMIN_ACCESS_KEY
        session["access_level"] = "admin"
        session["operations_dashboard_quarter"] = "q2"
        session.save()

        response = self.client.get(reverse("sharepoint_tracker"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["entries"]), 1)
        self.assertEqual(response.context["entries"][0].client_name, "Client A")

    def test_dashboard_does_not_render_outstanding_card(self):
        session = self.client.session
        session["access_key"] = ADMIN_ACCESS_KEY
        session["access_level"] = "admin"
        session.save()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending Reports")
        self.assertNotContains(response, "Outstanding")

    def test_second_quarter_dashboard_keeps_real_status_for_team(self):
        ClientReport.objects.create(
            client_name="Client Q2",
            crm_name="CRM Q2",
            operations_assignee="Ops Q2",
            status_phase=StatusPhase.REVIEWED,
        )

        session = self.client.session
        session["access_key"] = TEAM_ACCESS_KEY
        session["access_level"] = "team"
        session.save()

        response = self.client.post(
            reverse("unlock_access"),
            {
                "passkey": TEAM_ACCESS_KEY,
                "quarter": "q2",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_quarter"], "q2")
        self.assertGreaterEqual(response.context["summary"]["total_clients"], 1)
        self.assertEqual(response.context["summary"]["reviewed_count"], 1)

    def test_second_quarter_dashboard_keeps_real_status_for_admin(self):
        ClientReport.objects.create(
            client_name="Client Admin Q2",
            crm_name="CRM Q2",
            operations_assignee="Ops Q2",
            status_phase=StatusPhase.REVIEWED,
        )

        session = self.client.session
        session["access_key"] = ADMIN_ACCESS_KEY
        session["access_level"] = "admin"
        session["operations_dashboard_quarter"] = "q2"
        session.save()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_quarter"], "q2")
        self.assertEqual(response.context["summary"]["reviewed_count"], 1)

    def test_admin_can_update_report_status_in_second_quarter(self):
        report = ClientReport.objects.create(
            client_name="Client Edit Q2",
            crm_name="CRM Q2",
            operations_assignee="Ops Q2",
            status_phase=StatusPhase.PENDING,
        )

        session = self.client.session
        session["access_key"] = ADMIN_ACCESS_KEY
        session["access_level"] = "admin"
        session["operations_dashboard_quarter"] = "q2"
        session.save()

        response = self.client.post(
            reverse("report_edit", kwargs={"pk": report.pk}),
            {
                "due_date": "",
                "status_phase": StatusPhase.SENT_TO_CLIENT,
                "notes": "Updated in second quarter",
            },
            follow=True,
        )

        report.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(report.status_phase, StatusPhase.SENT_TO_CLIENT)
        self.assertEqual(response.context["selected_quarter"], "q2")


class SharePointTrackerImportTests(TestCase):
    def test_import_updates_existing_entries_from_workbook(self):
        SharePointTrackerEntry.objects.create(client_name="Client A", crm_name="CRM 1")

        with NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
            workbook_path = Path(handle.name)

        try:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "1Q26"
            sheet.append(["Client Name", "CRM", "Alternate", "Word", "Excel ", "PDF ", "Due Date"])
            sheet.append([None, None, None, 50, 46, 0, None])
            sheet.append(["Client A", "CRM 1", "Alt 1", "✓", "✓", "✓", "Dec 2026"])
            workbook.save(workbook_path)

            command = ImportSharePointTrackerCommand()
            command.import_from_workbook(workbook_path)

            entry = SharePointTrackerEntry.objects.get(client_name="Client A")
            self.assertTrue(entry.word_submitted)
            self.assertTrue(entry.excel_submitted)
            self.assertTrue(entry.pdf_submitted)
            self.assertEqual(entry.status, SharePointTrackerEntry.Status.COMPLETED)
        finally:
            workbook_path.unlink(missing_ok=True)


class SharePointTrackerEntryTests(TestCase):
    def test_status_for_word_only(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client A",
            crm_name="CRM 1",
            word_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_WORD)

    def test_status_for_pdf_only(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client B",
            crm_name="CRM 2",
            pdf_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_PDF)

    def test_status_for_excel_only(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client C",
            crm_name="CRM 3",
            excel_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_EXCEL)

    def test_status_for_word_and_excel(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client D",
            crm_name="CRM 4",
            word_submitted=True,
            excel_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_WORD_AND_EXCEL)

    def test_status_for_word_and_pdf(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client E",
            crm_name="CRM 5",
            word_submitted=True,
            pdf_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_WORD_AND_PDF)

    def test_status_for_excel_and_pdf(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client F",
            crm_name="CRM 6",
            excel_submitted=True,
            pdf_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_EXCEL_AND_PDF)

    def test_status_for_completed(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client C",
            crm_name="CRM 3",
            word_submitted=True,
            excel_submitted=True,
            pdf_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.COMPLETED)
