from django import forms

from .models import ActionItem


class ActionItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        allow_client_edit = kwargs.pop('allow_client_edit', False)
        super().__init__(*args, **kwargs)

        if not allow_client_edit:
            self.fields['client'].widget.attrs['readonly'] = 'readonly'

    class Meta:
        model = ActionItem
        fields = [
            'client',
            'action_item',
            'status',
            'owner',
            'date_received',
            'target_date',
            'completion_date',
            'update_prev_week',
            'update_this_week',
        ]
        widgets = {
            'client': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
            }),
            'action_item': forms.Textarea(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'rows': 3,
            }),
            'status': forms.Select(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
            }),
            'owner': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
            }),
            'date_received': forms.DateInput(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'type': 'date',
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'type': 'date',
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'type': 'date',
            }),
            'update_prev_week': forms.Textarea(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'rows': 3,
            }),
            'update_this_week': forms.Textarea(attrs={
                'class': 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'rows': 3,
            }),
        }
