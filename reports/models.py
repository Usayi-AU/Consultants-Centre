from django.db import models


class StatusPhase(models.TextChoices):
    PENDING = "pending", "Pending"
    SUBMITTED = "submitted", "Submitted"
    REVIEWED = "reviewed", "Reviewed"
    SENT_TO_CLIENT = "sent_to_client", "Sent to Client"


class ClientReport(models.Model):
    client_name = models.CharField(max_length=255, unique=True)
    crm_name = models.CharField(max_length=120)
    operations_assignee = models.CharField(max_length=120)
    due_date = models.DateField(null=True, blank=True)
    status_phase = models.CharField(
        max_length=20,
        choices=StatusPhase.choices,
        default=StatusPhase.PENDING,
    )
    submitted_tick = models.BooleanField(default=False)
    reviewed_tick = models.BooleanField(default=False)
    sent_to_client_tick = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["operations_assignee", "crm_name", "client_name"]

    def __str__(self):
        return self.client_name

    @staticmethod
    def flags_for_phase(phase):
        if phase == StatusPhase.SENT_TO_CLIENT:
            return True, True, True
        if phase == StatusPhase.REVIEWED:
            return True, True, False
        if phase == StatusPhase.SUBMITTED:
            return True, False, False
        return False, False, False

    @classmethod
    def phase_from_flags(cls, submitted_tick, reviewed_tick, sent_to_client_tick):
        if sent_to_client_tick:
            return StatusPhase.SENT_TO_CLIENT
        if reviewed_tick:
            return StatusPhase.REVIEWED
        if submitted_tick:
            return StatusPhase.SUBMITTED
        return StatusPhase.PENDING

    def sync_flags_from_phase(self):
        self.submitted_tick, self.reviewed_tick, self.sent_to_client_tick = self.flags_for_phase(self.status_phase)

    @property
    def completion_state(self):
        return self.get_status_phase_display()

    @property
    def status_badge_class(self):
        return {
            StatusPhase.PENDING: "bg-slate-100 text-slate-700 ring-slate-200",
            StatusPhase.SUBMITTED: "bg-amber-100 text-amber-800 ring-amber-200",
            StatusPhase.REVIEWED: "bg-sky-100 text-sky-800 ring-sky-200",
            StatusPhase.SENT_TO_CLIENT: "bg-emerald-100 text-emerald-800 ring-emerald-200",
        }.get(self.status_phase, "bg-slate-100 text-slate-700 ring-slate-200")

    def save(self, *args, **kwargs):
        self.sync_flags_from_phase()
        super().save(*args, **kwargs)
