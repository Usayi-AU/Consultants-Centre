import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .chat_service import ChatService
from .models import Proposal, SharePointTrackerEntry
from .permissions import ALT_ADMIN_ACCESS_KEY


class ChatAssistantTests(TestCase):
    def test_chat_api_accepts_anonymous_requests(self):
        response = self.client.post(
            reverse("chat_api"),
            data=json.dumps({"message": "Hello"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("reply", payload)
        self.assertTrue(payload["reply"])

    def test_chat_api_returns_reply_for_authenticated_user(self):
        user = get_user_model().objects.create_user(username="assistantuser", password="strongpass")
        self.client.force_login(user)

        response = self.client.post(
            reverse("chat_api"),
            data=json.dumps({"message": "What services do you offer?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("reply", payload)
        self.assertTrue(payload["reply"])

    def test_build_context_includes_dashboard_counts_for_report_questions(self):
        service = ChatService()
        context = {
            "dashboard_summary": {
                "total_reports": 12,
                "submitted": 3,
                "reviewed": 2,
                "sent": 5,
                "pending": 2,
            },
            "sent_report_clients": ["Client A", "Client B"],
        }

        prompt = service.build_context("How many reports were sent to clients?", context)

        self.assertIn("total reports: 12", prompt.lower())
        self.assertIn("sent to client: 5", prompt.lower())
        self.assertIn("client a", prompt.lower())


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
