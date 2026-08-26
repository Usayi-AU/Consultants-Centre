from collections import defaultdict
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.db.models import Q

from .forms import ActionItemForm
from .models import ActionItem, ActionItemHistory, SummaryMetric, STATUS_DONE
from .forms import MeetingLogForm, MeetingActionPointForm
from .models import MeetingLog, MeetingActionPoint, MeetingFeedbackSeenState
from reports.trail import build_change_details, log_dashboard_event


ACCESS_SESSION_KEY = 'crm_access'
GENERAL_PASSKEY = '10'
LEGACY_GENERAL_PASSKEY = '02'
ADMIN_PASSKEY = 'tari.crm@'
OWNER_NAMES = [
    'Isaac', 'Welcome', 'IsaacGT', 'Tino', 'Godfrey',
    'Arnold', 'Tatenda', 'Eustina', 'Elvis', 'Tari', 'Owen', 'Simba',
]


def normalize_access_value(value):
    return str(value or '').strip().lower()


def get_owner_lookup():
    lookup = {normalize_access_value(name): name for name in OWNER_NAMES}
    owners = ActionItem.objects.exclude(owner__isnull=True).exclude(owner='').values_list('owner', flat=True).distinct()
    for owner in owners:
        lookup.setdefault(normalize_access_value(owner), owner)
    return lookup


def can_manage_meetings(access):
    return access['role'] in ('admin', 'owner')


def get_meetings_viewer_name(access):
    if access['role'] == 'owner' and access.get('owner'):
        return access['owner']
    if access['role'] == 'admin':
        return 'Admin'
    return None


def get_meeting_unseen_count_for_access(access):
    viewer_name = get_meetings_viewer_name(access)
    if not viewer_name:
        return 0

    state, _ = MeetingFeedbackSeenState.objects.get_or_create(viewer_name=viewer_name)
    meetings = MeetingLog.objects.all()
    if state.last_seen_at:
        meetings = meetings.filter(
            Q(created_at__gt=state.last_seen_at)
            | Q(created_at=state.last_seen_at, pk__gt=state.last_seen_meeting_pk)
        )
    return meetings.count()


def mark_meetings_seen_for_access(access):
    viewer_name = get_meetings_viewer_name(access)
    if not viewer_name:
        return

    relevant_meetings = MeetingLog.objects.all().order_by('-created_at', '-pk')

    latest = relevant_meetings.first()
    state, _ = MeetingFeedbackSeenState.objects.get_or_create(viewer_name=viewer_name)
    if latest:
        state.last_seen_at = latest.created_at
        state.last_seen_meeting_pk = latest.pk
    else:
        state.last_seen_at = timezone.now()
        state.last_seen_meeting_pk = 0
    state.save(update_fields=['last_seen_at', 'last_seen_meeting_pk'])


def get_crm_access(request):
    access = request.session.get(ACCESS_SESSION_KEY)
    if not access:
        return {
            'authenticated': False,
            'role': 'guest',
            'owner': None,
            'label': 'Guest',
        }

    role = access.get('role')
    if role == 'owner':
        return {
            'authenticated': True,
            'role': 'owner',
            'owner': access.get('owner'),
            'label': access.get('owner') or 'Owner',
        }

    if role == 'admin':
        return {
            'authenticated': True,
            'role': 'admin',
            'owner': None,
            'label': 'Admin',
        }

    return {
        'authenticated': True,
        'role': 'general',
        'owner': None,
        'label': 'General',
    }


def set_crm_access(request, role, owner=None):
    data = {'role': role}
    if owner:
        data['owner'] = owner
    request.session[ACCESS_SESSION_KEY] = data


def resolve_passkey(passkey):
    token = normalize_access_value(passkey)

    if token in {
        normalize_access_value(GENERAL_PASSKEY),
        normalize_access_value(LEGACY_GENERAL_PASSKEY),
    }:
        return {'role': 'general', 'message': 'General unlock access is enabled.'}

    if token == normalize_access_value(ADMIN_PASSKEY):
        return {'role': 'admin', 'message': 'Admin unlock access is enabled.'}

    owner_lookup = get_owner_lookup()
    owner = owner_lookup.get(token)
    if owner:
        return {'role': 'owner', 'owner': owner, 'message': f'{owner} access is enabled.'}

    return None


def crm_access_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        access = get_crm_access(request)
        if not access['authenticated']:
            return redirect('crm:unlock_access')
        return view_func(request, *args, **kwargs)

    return wrapped


def get_actor_label(request):
    access = get_crm_access(request)
    if access['role'] == 'admin':
        return 'Admin'
    if access['role'] == 'owner':
        return access['owner'] or 'Owner'
    return 'General'


def format_history_entry(action, actor_label, action_item=None, form=None):
    if action == 'create':
        return (
            f"Created by {actor_label} • Client: {action_item.client} • "
            f"Owner: {action_item.owner} • Status: {action_item.status}"
        )

    if form and form.changed_data:
        detail = build_change_details(
            form,
            {
                'client': 'Client',
                'action_item': 'Action Item',
                'status': 'Status',
                'owner': 'Owner',
                'date_received': 'Date Received',
                'target_date': 'Target Date',
                'update_prev_week': 'Update Prev Week',
                'update_this_week': 'Update This Week',
                'completion_date': 'Completion Date',
            },
        )
        return f"Updated by {actor_label} • {detail}"

    return f"Updated by {actor_label} • updated fields"


def get_filtered_items(request):
    access = get_crm_access(request)
    items = ActionItem.objects.all()
    if access['role'] == 'owner':
        items = items.filter(owner=access['owner'])
    return items


def can_edit_action_item(request, item):
    access = get_crm_access(request)
    if access['role'] == 'admin':
        return True
    return access['role'] == 'owner' and access['owner'] == item.owner


def unlock_access(request):
    access = get_crm_access(request)
    if access['authenticated']:
        return redirect('crm:dashboard')

    if request.method == 'POST':
        result = resolve_passkey(request.POST.get('passkey'))
        if result:
            set_crm_access(request, result['role'], result.get('owner'))
            messages.success(request, result['message'])
            return redirect('crm:dashboard')

        messages.error(request, 'Invalid passkey.')

    return render(request, 'crm/unlock_access.html', {'access_state': access})


def meetings_unlock(request):
    access = get_crm_access(request)
    if can_manage_meetings(access):
        return redirect('crm:meetings_list')

    if request.method == 'POST':
        result = resolve_passkey(request.POST.get('passkey'))
        if result and result['role'] in {'admin', 'owner'}:
            set_crm_access(request, result['role'], result.get('owner'))
            mark_meetings_seen_for_access({'role': result['role'], 'owner': result.get('owner')})
            messages.success(request, f"{result['message']} Meeting Feedback access granted.")
            return redirect('crm:meetings_list')

        if result and result['role'] == 'general':
            messages.error(request, 'General passkey cannot access Meeting Feedback. Use your named passkey or admin passkey.')
        else:
            messages.error(request, 'Invalid passkey for Meeting Feedback.')

    return render(request, 'crm/meetings_unlock.html', {
        'access_state': access,
    })


def exit_dashboard(request):
    if request.method in ('GET', 'POST'):
        request.session.pop(ACCESS_SESSION_KEY, None)
        request.session.modified = True
        messages.success(request, 'Session cleared. You have exited Client Relations.')

    return redirect('crm:unlock_access')


@crm_access_required
def dashboard(request):
    access = get_crm_access(request)
    qs = get_filtered_items(request)
    summary_metrics = SummaryMetric.objects.all()
    active_items = qs.exclude(status__iexact=STATUS_DONE)
    completed_items = qs.filter(status__iexact=STATUS_DONE)
    today = timezone.localdate()

    meeting_preview = []
    meetings_total = 0
    meetings_open_actions = 0
    meetings_due_soon = 0

    if can_manage_meetings(access):
        meeting_preview = list(MeetingLog.objects.order_by('-meeting_date', '-created_at')[:3])
        meetings_total = MeetingLog.objects.count()
        open_actions = MeetingActionPoint.objects.exclude(status__iexact=STATUS_DONE)
        meetings_open_actions = open_actions.count()
        meetings_due_soon = open_actions.filter(
            target_date__gte=today,
            target_date__lte=today + timedelta(days=7),
        ).count()

    recent_updates = []
    if access['role'] == 'admin':
        recent_updates = ActionItemHistory.objects.select_related('action_item').order_by('-timestamp')[:10]

    context = {
        'summary_metrics': summary_metrics,
        'active_items_count': active_items.count(),
        'completed_items_count': completed_items.count(),
        'meetings_unseen_count': get_meeting_unseen_count_for_access(access),
        'meetings_total': meetings_total,
        'meetings_open_actions': meetings_open_actions,
        'meetings_due_soon': meetings_due_soon,
        'meeting_preview': meeting_preview,
        'recent_updates': recent_updates,
        'access_state': access,
    }
    return render(request, 'crm/dashboard.html', context)


@crm_access_required
def create_action_item(request):
    access = get_crm_access(request)
    if access['role'] not in {'admin', 'owner'}:
        return HttpResponseForbidden('Only admin and owners may create action items.')

    if request.method == 'POST':
        form = ActionItemForm(request.POST, allow_client_edit=True)
        if form.is_valid():
            action_item = form.save(commit=False)
            if access['role'] == 'owner':
                action_item.owner = access['owner']
            action_item.save()
            ActionItemHistory.objects.create(
                action_item=action_item,
                changes=format_history_entry('create', get_actor_label(request), action_item=action_item),
            )
            messages.success(request, 'Action item created successfully.')
            return redirect('crm:client_detail', client_name=action_item.client)
    else:
        form = ActionItemForm(allow_client_edit=True)
        if access['role'] == 'owner':
            form.initial['owner'] = access['owner']
            form.fields['owner'].widget.attrs['readonly'] = 'readonly'

    return render(request, 'crm/actionitem_form.html', {
        'form': form,
        'is_create': True,
        'submit_label': 'Create Action Item',
        'page_title': 'Create action item',
        'page_subtitle': 'Add a new client follow-up and keep your team aligned.',
        'cancel_url': 'crm:client_action_items',
        'access_state': access,
    })


@crm_access_required
def client_action_items(request):
    q = request.GET.get('q', '').strip()
    qs = get_filtered_items(request).exclude(status__iexact=STATUS_DONE)
    if q:
        qs = qs.filter(Q(client__icontains=q) | Q(action_item__icontains=q) | Q(owner__icontains=q))
    action_items = qs.order_by('client', 'target_date')
    grouped = defaultdict(list)
    for item in action_items:
        grouped[item.client or 'Unknown Client'].append(item)
    grouped_items = list(grouped.items())
    access = get_crm_access(request)
    return render(request, 'crm/client_action_items.html', {
        'grouped_items': grouped_items,
        'q': q,
        'access_state': access,
    })


@crm_access_required
def client_hub(request):
    q = request.GET.get('q', '').strip()
    clients = defaultdict(lambda: {'completed': [], 'ongoing': []})
    items = get_filtered_items(request)
    if q:
        items = items.filter(Q(client__icontains=q) | Q(action_item__icontains=q) | Q(owner__icontains=q))
    for item in items:
        key = item.client or 'Unknown Client'
        if item.is_completed:
            clients[key]['completed'].append(item)
        else:
            clients[key]['ongoing'].append(item)

    clients_items = list(clients.items())
    access = get_crm_access(request)
    return render(request, 'crm/client_hub.html', {
        'clients_items': clients_items,
        'q': q,
        'access_state': access,
    })


@crm_access_required
def client_detail(request, client_name):
    items = get_filtered_items(request).filter(client=client_name)
    completed = items.filter(status__iexact=STATUS_DONE)
    ongoing = items.exclude(status__iexact=STATUS_DONE)
    access = get_crm_access(request)
    return render(request, 'crm/client_detail.html', {
        'client_name': client_name,
        'completed_items': completed,
        'ongoing_items': ongoing,
        'access_state': access,
    })


@crm_access_required
def edit_action_item(request, pk):
    item = get_object_or_404(ActionItem, pk=pk)
    if not can_edit_action_item(request, item):
        return HttpResponseForbidden('You can only edit your own action items.')

    if request.method == 'POST':
        form = ActionItemForm(request.POST, instance=item)
        if form.is_valid():
            action_item = form.save(commit=False)
            action_item.updated_by = None
            action_item.updated_at = timezone.now()
            action_item.save()

            ActionItemHistory.objects.create(
                action_item=action_item,
                changes=format_history_entry('edit', get_actor_label(request), form=form),
            )

            messages.success(request, 'Action item saved successfully.')
            return redirect('crm:client_detail', client_name=action_item.client)
    else:
        form = ActionItemForm(instance=item)

    access = get_crm_access(request)
    return render(request, 'crm/actionitem_form.html', {
        'form': form,
        'item': item,
        'is_create': False,
        'submit_label': 'Save Changes',
        'page_title': 'Edit action item',
        'page_subtitle': 'Refine client follow-ups and keep the record current.',
        'cancel_url': 'crm:client_detail',
        'cancel_args': [item.client],
        'is_admin': access['role'] == 'admin',
        'access_state': access,
    })


@crm_access_required
def admin_activity(request):
    access = get_crm_access(request)
    if access['role'] != 'admin':
        return HttpResponseForbidden('Only admin may view activity history.')

    history = ActionItemHistory.objects.select_related('action_item').order_by('-timestamp')
    return render(request, 'crm/admin_activity.html', {
        'history': history,
        'access_state': access,
    })


@crm_access_required
def delete_action_item(request, pk):
    if get_crm_access(request)['role'] != 'admin':
        return HttpResponseForbidden('Only admin may delete action items.')
    item = get_object_or_404(ActionItem, pk=pk)
    if request.method == 'POST':
        record_label = item.client
        action_label = item.action_item[:140]
        item.delete()
        log_dashboard_event(
            dashboard_key='client_relations',
            event_type='deleted',
            section_label='Action Items',
            record_label=record_label,
            summary=f"Deleted action item for {record_label}.",
            details=action_label,
            actor_label='CRM Admin',
        )
        messages.success(request, 'Action item deleted.')
        return redirect('crm:client_action_items')
    return render(request, 'crm/actionitem_confirm_delete.html', {'item': item})


@crm_access_required
def delete_history(request, pk):
    access = get_crm_access(request)
    if access['role'] != 'admin':
        return HttpResponseForbidden('Only admin may delete history records.')

    history_entry = get_object_or_404(ActionItemHistory, pk=pk)
    if request.method == 'POST':
        history_entry.delete()
        messages.success(request, 'History record deleted.')
        return redirect('crm:admin_activity')

    return render(request, 'crm/history_confirm_delete.html', {
        'history_entry': history_entry,
        'access_state': access,
    })


def get_filtered_meetings(request):
    return MeetingLog.objects.all()


@crm_access_required
def meetings_list(request):
    access = get_crm_access(request)
    if not can_manage_meetings(access):
        messages.info(request, 'Please unlock Meeting Feedback using your named passkey or admin passkey.')
        return redirect('crm:meetings_unlock')

    today = timezone.localdate()
    q = request.GET.get('q', '').strip()
    scope = request.GET.get('scope', 'all').strip().lower() or 'all'

    meetings = get_filtered_meetings(request).prefetch_related('action_points')
    if q:
        meetings = meetings.filter(Q(client__icontains=q) | Q(summary__icontains=q) | Q(attendees__icontains=q))

    if scope == 'open':
        meetings = meetings.filter(action_points__status__in=[STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_ON_HOLD]).distinct()
    elif scope == 'overdue':
        meetings = meetings.filter(action_points__target_date__lt=today).exclude(action_points__status__iexact=STATUS_DONE).distinct()
    elif scope == 'due_soon':
        meetings = meetings.filter(
            action_points__target_date__gte=today,
            action_points__target_date__lte=today + timedelta(days=7),
        ).exclude(action_points__status__iexact=STATUS_DONE).distinct()

    all_open_actions = MeetingActionPoint.objects.exclude(status__iexact=STATUS_DONE)
    stats = {
        'total_meetings': MeetingLog.objects.count(),
        'open_actions': all_open_actions.count(),
        'overdue_actions': all_open_actions.filter(target_date__lt=today).count(),
        'due_soon_actions': all_open_actions.filter(target_date__gte=today, target_date__lte=today + timedelta(days=7)).count(),
    }

    return render(request, 'crm/meetings_list.html', {
        'meetings': meetings,
        'q': q,
        'scope': scope,
        'stats': stats,
        'access_state': access,
    })


@crm_access_required
def create_meeting(request):
    access = get_crm_access(request)
    if not can_manage_meetings(access):
        messages.info(request, 'Please unlock Meeting Feedback before logging meetings.')
        return redirect('crm:meetings_unlock')
    if request.method == 'POST':
        form = MeetingLogForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            if access['role'] == 'owner' and not meeting.logged_by:
                meeting.logged_by = access['owner']
            meeting.save()
            log_dashboard_event(
                dashboard_key='client_relations',
                event_type='created',
                section_label='Meeting Feedback',
                record_label=meeting.client,
                summary=f"Logged a meeting for {meeting.client}.",
                details=meeting.summary[:200],
                actor_label=get_actor_label(request),
            )
            messages.success(request, 'Meeting logged successfully.')
            return redirect('crm:meeting_detail', pk=meeting.pk)
    else:
        form = MeetingLogForm(initial={'meeting_date': timezone.localdate(), 'logged_by': access.get('owner') or ''})

    return render(request, 'crm/meeting_form.html', {
        'form': form,
        'submit_label': 'Log Meeting',
        'page_title': 'Log a client meeting',
        'page_subtitle': 'Capture meeting notes and raise action items for your team.',
        'access_state': access,
    })


@crm_access_required
def meeting_detail(request, pk):
    meeting = get_object_or_404(MeetingLog, pk=pk)
    access = get_crm_access(request)
    if not can_manage_meetings(access):
        messages.info(request, 'Please unlock Meeting Feedback to view meeting details.')
        return redirect('crm:meetings_unlock')
    action_form = MeetingActionPointForm()

    if request.method == 'POST':
        action_form = MeetingActionPointForm(request.POST)
        if action_form.is_valid():
            action_point = action_form.save(commit=False)
            action_point.meeting = meeting
            action_point.save()
            action_point.sync_linked_action_item()
            log_dashboard_event(
                dashboard_key='client_relations',
                event_type='created',
                section_label='Meeting Action Item',
                record_label=meeting.client,
                summary=f"Added action item for {meeting.client} from meeting on {meeting.meeting_date}.",
                details=action_point.description[:200],
                actor_label=get_actor_label(request),
            )
            messages.success(request, 'Action item added and linked to the Client Relations Dashboard.')
            return redirect('crm:meeting_detail', pk=meeting.pk)

    action_points = meeting.action_points.all()
    return render(request, 'crm/meeting_detail.html', {
        'meeting': meeting,
        'action_points': action_points,
        'action_form': action_form,
        'access_state': access,
    })


@crm_access_required
def edit_meeting_action_point(request, meeting_pk, pk):
    meeting = get_object_or_404(MeetingLog, pk=meeting_pk)
    action_point = get_object_or_404(MeetingActionPoint, pk=pk, meeting=meeting)
    access = get_crm_access(request)
    if not can_manage_meetings(access):
        messages.info(request, 'Please unlock Meeting Feedback to edit action items.')
        return redirect('crm:meetings_unlock')

    if request.method == 'POST':
        form = MeetingActionPointForm(request.POST, instance=action_point)
        if form.is_valid():
            action_point = form.save()
            action_point.sync_linked_action_item()
            log_dashboard_event(
                dashboard_key='client_relations',
                event_type='updated',
                section_label='Meeting Action Item',
                record_label=meeting.client,
                summary=f"Updated meeting action item for {meeting.client}.",
                details=action_point.description[:200],
                actor_label=get_actor_label(request),
            )
            messages.success(request, 'Action item updated and synced with the Client Relations Dashboard.')
            return redirect('crm:meeting_detail', pk=meeting.pk)
    else:
        form = MeetingActionPointForm(instance=action_point)

    return render(request, 'crm/meeting_action_form.html', {
        'form': form,
        'meeting': meeting,
        'action_point': action_point,
        'access_state': access,
    })


@crm_access_required
def delete_meeting(request, pk):
    access = get_crm_access(request)
    if access['role'] != 'admin':
        return HttpResponseForbidden('Only admin may delete meeting feedback.')

    meeting = get_object_or_404(MeetingLog, pk=pk)
    if request.method == 'POST':
        record_label = meeting.client
        meeting.delete()
        log_dashboard_event(
            dashboard_key='client_relations',
            event_type='deleted',
            section_label='Meeting Feedback',
            record_label=record_label,
            summary=f"Deleted meeting feedback for {record_label}.",
            actor_label='CRM Admin',
        )
        messages.success(request, 'Meeting feedback deleted.')
        return redirect('crm:meetings_list')

    return render(request, 'crm/meeting_confirm_delete.html', {
        'meeting': meeting,
        'access_state': access,
    })
