from django.test import TestCase

from .models import Proposal, SharePointTrackerEntry


class ProposalTests(TestCase):
    def test_status_badge_class_is_styled_for_pending(self):
        proposal = Proposal.objects.create(
            proposal_name="Sample proposal",
            date="2026-01-12",
            status="preliminary",
        )

        self.assertEqual(proposal.status_badge_class, "bg-amber-100 text-amber-800 ring-amber-200")


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
