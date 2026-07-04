from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from reports.models import Proposal, ProposalDocument


class Command(BaseCommand):
    help = "Seed proposal records and attach documents from the alternative investments workspace folder."

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]
        source_dir = base_dir / "RE_ ALTERNATIVE INVESTMENTS-WORKFLOW DASHBOARD"

        proposals = [
            {
                "date": "2025-12-01",
                "proposal_name": "Glenforest Land Development Project",
                "status": "preliminary",
                "description": "Received from ABCAM. Preliminary analysis done, awaiting finalisation upon provision of additional information requested.",
                "document_candidates": [
                    source_dir / "2025 ABCAM Glenforest Land_Prospectus.pdf",
                ],
            },
            {
                "date": "2026-02-19",
                "proposal_name": "Eagle Mortgage Pass Through Fund",
                "status": "under_review",
                "description": "Analysis done pending final review.",
                "document_candidates": [
                    source_dir / "Eagle Mortgage Pass-Through Fund Prospectus (EAM COPY AFTER SECZIM COMMENTS clean copy).pdf",
                ],
            },
            {
                "date": "2026-05-05",
                "proposal_name": "Dominium Global Fund",
                "status": "preliminary",
                "description": "Preliminary analysis done, awaiting finalisation upon provision of additional information requested.",
                "document_candidates": [
                    source_dir / "Fw_ Dominium Global Fund - Offshore Investment" / "DGF PROSPECTUS.pdf",
                    source_dir / "Fw_ Dominium Global Fund - Offshore Investment" / "Dominium Global Fund DD Questionnaire.docx",
                ],
            },
        ]

        for proposal_data in proposals:
            proposal, created = Proposal.objects.get_or_create(
                proposal_name=proposal_data["proposal_name"],
                defaults={
                    "date": proposal_data["date"],
                    "status": proposal_data["status"],
                    "description": proposal_data["description"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created proposal: {proposal.proposal_name}"))
            else:
                proposal.date = proposal_data["date"]
                proposal.status = proposal_data["status"]
                proposal.description = proposal_data["description"]
                proposal.save()

            for candidate in proposal_data["document_candidates"]:
                if not candidate.exists():
                    continue
                if proposal.documents.filter(file__icontains=candidate.name).exists():
                    continue
                with candidate.open("rb") as handle:
                    ProposalDocument.objects.create(
                        proposal=proposal,
                        file=File(handle, name=candidate.name),
                        document_name=candidate.name,
                    )
        self.stdout.write(self.style.SUCCESS("Proposal seed complete."))
