from django.test import TestCase

from .models import SharePointTrackerEntry


class SharePointTrackerEntryTests(TestCase):
    def test_status_for_word_only(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client A",
            crm_name="CRM 1",
            word_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_WORD)

    def test_status_for_word_and_excel(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client B",
            crm_name="CRM 2",
            word_submitted=True,
            excel_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.SUBMITTED_WORD_AND_EXCEL)

    def test_status_for_completed(self):
        entry = SharePointTrackerEntry.objects.create(
            client_name="Client C",
            crm_name="CRM 3",
            word_submitted=True,
            excel_submitted=True,
            pdf_submitted=True,
        )

        self.assertEqual(entry.status, SharePointTrackerEntry.Status.COMPLETED)
