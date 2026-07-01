from django.db import models


class SharePointTrackerEntry(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUBMITTED_WORD = "submitted_word", "Submitted Word"
        SUBMITTED_WORD_AND_EXCEL = "submitted_word_and_excel", "Submitted Word and Excel"
        COMPLETED = "completed", "Completed"

    client_name = models.CharField(max_length=255, unique=True)
    crm_name = models.CharField(max_length=120, blank=True)
    alternate_name = models.CharField(max_length=120, blank=True)
    word_submitted = models.BooleanField(default=False)
    excel_submitted = models.BooleanField(default=False)
    pdf_submitted = models.BooleanField(default=False)
    due_date = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client_name"]

    def __str__(self):
        return self.client_name

    def sync_status(self):
        if self.word_submitted and self.excel_submitted and self.pdf_submitted:
            self.status = self.Status.COMPLETED
        elif self.word_submitted and self.excel_submitted:
            self.status = self.Status.SUBMITTED_WORD_AND_EXCEL
        elif self.word_submitted:
            self.status = self.Status.SUBMITTED_WORD
        else:
            self.status = self.Status.PENDING

    @property
    def status_badge_class(self):
        return {
            self.Status.PENDING: "bg-slate-100 text-slate-700 ring-slate-200",
            self.Status.SUBMITTED_WORD: "bg-amber-100 text-amber-800 ring-amber-200",
            self.Status.SUBMITTED_WORD_AND_EXCEL: "bg-sky-100 text-sky-800 ring-sky-200",
            self.Status.COMPLETED: "bg-emerald-100 text-emerald-800 ring-emerald-200",
        }.get(self.status, "bg-slate-100 text-slate-700 ring-slate-200")

    def save(self, *args, **kwargs):
        self.sync_status()
        super().save(*args, **kwargs)


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


class CRMActionStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "Work in Progress"
    COMPLETED = "completed", "Completed"


class CRMHistoryAction(models.TextChoices):
    CREATED = "created", "Created"
    UPDATED = "updated", "Updated"
    CLEARED = "cleared", "Cleared"
    DELETED = "deleted", "Deleted"
    IMPORTED = "imported", "Imported"


class CRMActionItem(models.Model):
    client_name = models.CharField(max_length=255)
    crm_owner = models.CharField(max_length=120)
    action_item = models.TextField()
    progress_update = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CRMActionStatus.choices, default=CRMActionStatus.IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client_name", "-updated_at"]

    def __str__(self):
        return f"{self.client_name} - {self.crm_owner}"

    @property
    def status_badge_class(self):
        return {
            CRMActionStatus.IN_PROGRESS: "bg-amber-100 text-amber-800 ring-amber-200",
            CRMActionStatus.COMPLETED: "bg-emerald-100 text-emerald-800 ring-emerald-200",
        }.get(self.status, "bg-slate-100 text-slate-700 ring-slate-200")


class CRMActionHistory(models.Model):
    action_item = models.ForeignKey(
        CRMActionItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_entries",
    )
    client_name = models.CharField(max_length=255)
    crm_owner = models.CharField(max_length=120)
    action_item_text = models.TextField()
    progress_update = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CRMActionStatus.choices, default=CRMActionStatus.IN_PROGRESS)
    action_type = models.CharField(max_length=20, choices=CRMHistoryAction.choices)
    actor_role = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client_name} - {self.action_type}"


class AltInvestmentStatus(models.TextChoices):
    GREEN = "green", "Green / On Track"
    AMBER = "amber", "Amber / Watch"
    RED = "red", "Red / Critical"


class AlternativeInvestmentItem(models.Model):
    investment_name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=120, blank=True)
    owner = models.CharField(max_length=120, blank=True)
    risk = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=AltInvestmentStatus.choices, default=AltInvestmentStatus.GREEN)
    status_headline = models.CharField(max_length=255, blank=True)
    status_headline_color = models.CharField(max_length=20, choices=AltInvestmentStatus.choices, default=AltInvestmentStatus.GREEN)
    investment_details = models.TextField(blank=True)
    pension_funds_invested = models.TextField(blank=True)
    status_developments = models.TextField(blank=True)
    performance = models.TextField(blank=True)
    summary_update = models.TextField(blank=True)
    detailed_review = models.TextField(blank=True)
    last_update = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["investment_name"]

    def __str__(self):
        return self.investment_name

    @property
    def status_badge_class(self):
        return {
            AltInvestmentStatus.GREEN: "bg-emerald-100 text-emerald-800 ring-emerald-200",
            AltInvestmentStatus.AMBER: "bg-amber-100 text-amber-800 ring-amber-200",
            AltInvestmentStatus.RED: "bg-rose-100 text-rose-800 ring-rose-200",
        }.get(self.status, "bg-slate-100 text-slate-700 ring-slate-200")

    @property
    def status_headline_badge_class(self):
        return {
            AltInvestmentStatus.GREEN: "bg-emerald-100 text-emerald-800",
            AltInvestmentStatus.AMBER: "bg-amber-100 text-amber-800",
            AltInvestmentStatus.RED: "bg-rose-100 text-rose-800",
        }.get(self.status_headline_color, "bg-slate-100 text-slate-700")


class DashboardSettings(models.Model):
    """Singleton-ish model to hold dashboard summary labels/values editable by admin."""
    manager_count_label = models.CharField(max_length=64, default="15+")
    pension_funds_label = models.CharField(max_length=64, default="48+")
    best_performers = models.PositiveIntegerField(default=0)
    distressed_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Dashboard Settings"

    def __str__(self):
        return "Dashboard settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class IPSReviewEntry(models.Model):
    fund_name = models.CharField(max_length=255)
    ic_crm = models.CharField(max_length=120, blank=True)
    administrator = models.CharField(max_length=255, blank=True)
    admin_crm = models.CharField(max_length=120, blank=True)
    member_fin_schedules = models.BooleanField(default=False)
    financial_review = models.BooleanField(default=False)
    replacement_ratios = models.CharField(max_length=255, blank=True)
    date_data_received = models.DateField(null=True, blank=True)
    date_sent_to_client = models.DateField(null=True, blank=True)
    workshop_required = models.BooleanField(default=False)
    asset_mgr_mandates = models.CharField(max_length=255, blank=True)
    status_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["fund_name"]

    def __str__(self):
        return self.fund_name


class TenderReferralEntry(models.Model):
    source_section = models.CharField(max_length=255, blank=True)
    client_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=255, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    email_address = models.CharField(max_length=255, blank=True)
    date_requested = models.DateField(null=True, blank=True)
    date_submitted = models.DateField(null=True, blank=True)
    status_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client_name"]

    def __str__(self):
        return self.client_name


class SelfGeneratedTarget(models.Model):
    source_section = models.CharField(max_length=255, blank=True)
    client_name = models.CharField(max_length=255)
    administrator = models.CharField(max_length=255, blank=True)
    business_target = models.CharField(max_length=255, blank=True)
    fund_size_usd_m = models.CharField(max_length=64, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    email_address = models.CharField(max_length=255, blank=True)
    date_requested = models.DateField(null=True, blank=True)
    date_submitted = models.DateField(null=True, blank=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client_name"]

    def __str__(self):
        return self.client_name
