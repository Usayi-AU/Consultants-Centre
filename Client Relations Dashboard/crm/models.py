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
