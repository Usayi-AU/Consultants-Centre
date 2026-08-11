from django.contrib import admin

from .models import ActionItem, ActionItemHistory, SummaryMetric, MeetingLog, MeetingActionPoint

@admin.register(SummaryMetric)
class SummaryMetricAdmin(admin.ModelAdmin):
    list_display = ('label', 'value')
    search_fields = ('label', 'value')

@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ('client', 'action_item', 'status', 'owner', 'target_date', 'completion_date', 'updated_by', 'updated_at')
    list_filter = ('status', 'owner', 'client')
    search_fields = ('client', 'action_item', 'owner')

@admin.register(ActionItemHistory)
class ActionItemHistoryAdmin(admin.ModelAdmin):
    list_display = ('action_item', 'changed_by', 'timestamp')
    search_fields = ('action_item__client', 'changed_by__username', 'changes')


class MeetingActionPointInline(admin.TabularInline):
    model = MeetingActionPoint
    extra = 0


@admin.register(MeetingLog)
class MeetingLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'meeting_date', 'logged_by', 'open_action_count')
    list_filter = ('client',)
    search_fields = ('client', 'summary', 'attendees')
    inlines = [MeetingActionPointInline]


@admin.register(MeetingActionPoint)
class MeetingActionPointAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'owner', 'status', 'target_date', 'linked_action_item')
    list_filter = ('status',)
    search_fields = ('description', 'owner', 'meeting__client')
