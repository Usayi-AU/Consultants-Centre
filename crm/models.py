from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()

STATUS_OPEN = 'Open'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_DONE = 'Done'
STATUS_ON_HOLD = 'On Hold'
STATUS_CHOICES = [
    (STATUS_OPEN, 'Open'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_DONE, 'Done'),
    (STATUS_ON_HOLD, 'On Hold'),
]

class SummaryMetric(models.Model):
    label = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return self.label

class ActionItem(models.Model):
    client = models.CharField(max_length=255)
    action_item = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_OPEN)
    owner = models.CharField(max_length=255)
    date_received = models.DateField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    update_prev_week = models.TextField(blank=True)
    update_this_week = models.TextField(blank=True)
    completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_action_items')

    class Meta:
        ordering = ['client', 'target_date']

    def __str__(self):
        return f"{self.client} — {self.action_item[:60]}"

    @property
    def is_completed(self):
        return self.status == STATUS_DONE or self.completion_date is not None

    def get_absolute_url(self):
        return reverse('crm:client_detail', args=[self.client])

class ActionItemHistory(models.Model):
    action_item = models.ForeignKey(ActionItem, related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action_item.client} updated by {self.changed_by or 'unknown'} at {self.timestamp}"


class MeetingLog(models.Model):
    """A record of a client meeting submitted by a CRM team member."""
    client = models.CharField(max_length=255)
    meeting_date = models.DateField()
    attendees = models.CharField(max_length=500, blank=True, help_text='Comma separated list of attendees')
    summary = models.TextField(blank=True, help_text='Key discussion points and outcomes')
    logged_by = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-meeting_date', '-created_at']

    def __str__(self):
        return f"{self.client} — {self.meeting_date}"

    @property
    def open_action_count(self):
        return self.action_points.exclude(status__iexact=STATUS_DONE).count()


class MeetingActionPoint(models.Model):
    """An action item raised during a meeting, mirrored into the Client Relations Dashboard."""
    meeting = models.ForeignKey(MeetingLog, related_name='action_points', on_delete=models.CASCADE)
    description = models.TextField()
    owner = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_OPEN)
    target_date = models.DateField(null=True, blank=True)
    linked_action_item = models.OneToOneField(
        ActionItem, null=True, blank=True, on_delete=models.SET_NULL, related_name='meeting_action_point'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date', 'created_at']

    def __str__(self):
        return f"{self.meeting.client} — {self.description[:60]}"

    def sync_linked_action_item(self):
        """Create or update the linked ActionItem so it surfaces on the Client Relations Dashboard."""
        if self.linked_action_item:
            item = self.linked_action_item
            item.client = self.meeting.client
            item.action_item = self.description
            item.owner = self.owner
            item.status = self.status
            item.target_date = self.target_date
            item.date_received = self.meeting.meeting_date
            if self.status == STATUS_DONE and not item.completion_date:
                item.completion_date = timezone_localdate()
            item.save()
        else:
            item = ActionItem.objects.create(
                client=self.meeting.client,
                action_item=self.description,
                owner=self.owner,
                status=self.status,
                target_date=self.target_date,
                date_received=self.meeting.meeting_date,
            )
            self.linked_action_item = item
            self.save(update_fields=['linked_action_item'])

    @property
    def days_until_due(self):
        if not self.target_date:
            return None
        return (self.target_date - timezone_localdate()).days

    @property
    def urgency(self):
        """Return one of: overdue, urgent, soon, normal, done, none."""
        if self.status == STATUS_DONE:
            return 'done'
        days = self.days_until_due
        if days is None:
            return 'none'
        if days < 0:
            return 'overdue'
        if days <= 2:
            return 'urgent'
        if days <= 7:
            return 'soon'
        return 'normal'

    @property
    def urgency_meta(self):
        mapping = {
            'overdue': {'label': 'Overdue', 'color': '#dc2626', 'bg': '#fee2e2', 'text': '#991b1b'},
            'urgent': {'label': 'Urgent', 'color': '#ea580c', 'bg': '#ffedd5', 'text': '#9a3412'},
            'soon': {'label': 'Due Soon', 'color': '#ca8a04', 'bg': '#fef9c3', 'text': '#854d0e'},
            'normal': {'label': 'On Track', 'color': '#16a34a', 'bg': '#dcfce7', 'text': '#166534'},
            'done': {'label': 'Completed', 'color': '#4f46e5', 'bg': '#e0e7ff', 'text': '#3730a3'},
            'none': {'label': 'No Due Date', 'color': '#64748b', 'bg': '#f1f5f9', 'text': '#334155'},
        }
        return mapping[self.urgency]


class MeetingFeedbackSeenState(models.Model):
    viewer_name = models.CharField(max_length=255, unique=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_meeting_pk = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['viewer_name']

    def __str__(self):
        return f"{self.viewer_name} seen at {self.last_seen_at or 'never'}"


def timezone_localdate():
    from django.utils import timezone
    return timezone.localdate()
