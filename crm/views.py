from collections import defaultdict
from functools import wraps

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.db.models import Q

from .forms import ActionItemForm
from .models import ActionItem, ActionItemHistory, SummaryMetric, STATUS_DONE


ACCESS_SESSION_KEY = 'crm_access'
GENERAL_PASSKEY = '02'
ADMIN_PASSKEY = 'tari.crm@'


def normalize_access_value(value):
    return str(value or '').strip().lower()


def get_owner_lookup():
    owners = ActionItem.objects.exclude(owner__isnull=True).exclude(owner='').values_list('owner', flat=True).distinct()
    lookup = {}
    for owner in owners:
        lookup[normalize_access_value(owner)] = owner
    return lookup


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

    if token == normalize_access_value(GENERAL_PASSKEY):
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

    changed_fields = ', '.join(form.changed_data) if form and form.changed_data else 'updated fields'
    return f"Updated by {actor_label} • {changed_fields}"


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


def exit_dashboard(request):
    if request.method in ('GET', 'POST'):
        request.session.pop(ACCESS_SESSION_KEY, None)
        request.session.modified = True
        messages.success(request, 'Session cleared. You have exited Client Relations.')

    try:
        reverse('consultancy_hub')
    except NoReverseMatch:
        return redirect('crm:unlock_access')
    return redirect('consultancy_hub')


@crm_access_required
def dashboard(request):
    access = get_crm_access(request)
    qs = get_filtered_items(request)
    summary_metrics = SummaryMetric.objects.all()
    active_items = qs.exclude(status__iexact=STATUS_DONE)
    completed_items = qs.filter(status__iexact=STATUS_DONE)

    recent_updates = []
    if access['role'] == 'admin':
        recent_updates = ActionItemHistory.objects.select_related('action_item').order_by('-timestamp')[:10]

    context = {
        'summary_metrics': summary_metrics,
        'active_items_count': active_items.count(),
        'completed_items_count': completed_items.count(),
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
        item.delete()
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
