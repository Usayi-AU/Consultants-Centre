from django import forms

from .models import AlternativeInvestmentItem, AltInvestmentStatus, CRMActionItem, CRMActionStatus, ClientReport, StatusPhase
from .models import IPSReviewEntry, TenderReferralEntry, SelfGeneratedTarget


class ReportStatusForm(forms.ModelForm):
    class Meta:
        model = ClientReport
        fields = ["due_date", "status_phase", "notes"]
        widgets = {
            "due_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "status_phase": forms.Select(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "notes": forms.TextInput(
                attrs={
                    "placeholder": "Optional note for the tracker",
                    "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500",
                }
            ),
        }

    def clean_status_phase(self):
        status_phase = self.cleaned_data["status_phase"]
        if status_phase not in StatusPhase.values:
            raise forms.ValidationError("Select a valid status phase.")
        return status_phase


class CRMActionItemCreateForm(forms.ModelForm):
    client_name = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
        ),
    )
    crm_owner = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
        ),
    )

    class Meta:
        model = CRMActionItem
        fields = ["client_name", "crm_owner", "action_item", "progress_update", "due_date"]
        widgets = {
            "action_item": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "progress_update": forms.Textarea(
                attrs={"rows": 2, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "due_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clients = sorted(
            [name for name in ClientReport.objects.values_list("client_name", flat=True).distinct() if name]
        )
        self.fields["client_name"].choices = [(name, name) for name in clients]

        if self.instance and self.instance.pk and self.instance.client_name and self.instance.client_name not in dict(self.fields["client_name"].choices):
            self.fields["client_name"].choices.append((self.instance.client_name, self.instance.client_name))

    def clean_crm_owner(self):
        crm_owner = self.cleaned_data["crm_owner"].strip()
        if not crm_owner:
            raise forms.ValidationError("Enter the CRM owner name.")
        return crm_owner


class CRMActionItemOwnerForm(forms.ModelForm):
    class Meta:
        model = CRMActionItem
        fields = ["action_item", "progress_update", "due_date"]
        widgets = {
            "action_item": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "progress_update": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "due_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
        }


class CRMActionItemAdminForm(CRMActionItemCreateForm):
    class Meta(CRMActionItemCreateForm.Meta):
        fields = ["client_name", "crm_owner", "action_item", "progress_update", "status", "due_date"]
        widgets = {
            **CRMActionItemCreateForm.Meta.widgets,
            "status": forms.Select(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        status_field = forms.Select(
            attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
        )
        self.fields["status"].widget = status_field

    def clean_status(self):
        status = self.cleaned_data["status"]
        if status not in CRMActionStatus.values:
            raise forms.ValidationError("Select a valid CRM action status.")
        return status


class AlternativeInvestmentItemForm(forms.ModelForm):
    class Meta:
        model = AlternativeInvestmentItem
        fields = [
            "investment_name",
            "category",
            "risk",
            "owner",
            "status",
            "status_headline",
            "status_headline_color",
            "investment_details",
            "pension_funds_invested",
            "status_developments",
            "performance",
            "summary_update",
            "detailed_review",
            "last_update",
            "next_review_date",
        ]
        widgets = {
            "investment_name": forms.TextInput(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "category": forms.TextInput(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "risk": forms.TextInput(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "owner": forms.TextInput(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "status": forms.Select(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "status_headline": forms.TextInput(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "status_headline_color": forms.Select(
                attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "investment_details": forms.Textarea(
                attrs={"rows": 8, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "pension_funds_invested": forms.Textarea(
                attrs={"rows": 8, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "status_developments": forms.Textarea(
                attrs={"rows": 8, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "performance": forms.Textarea(
                attrs={"rows": 8, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "summary_update": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "detailed_review": forms.Textarea(
                attrs={"rows": 6, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "last_update": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
            "next_review_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
            ),
        }

    def clean_status(self):
        status = self.cleaned_data["status"]
        if status not in AltInvestmentStatus.values:
            raise forms.ValidationError("Select a valid investment status.")
        return status


class DashboardSettingsForm(forms.Form):
    manager_count_label = forms.CharField(max_length=64, required=False)
    pension_funds_label = forms.CharField(max_length=64, required=False)
    best_performers = forms.IntegerField(min_value=0, required=False)
    distressed_count = forms.IntegerField(min_value=0, required=False)

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        initial = kwargs.pop("initial", {})
        if instance is not None:
            initial.setdefault("manager_count_label", getattr(instance, "manager_count_label", ""))
            initial.setdefault("pension_funds_label", getattr(instance, "pension_funds_label", ""))
            initial.setdefault("best_performers", getattr(instance, "best_performers", 0))
            initial.setdefault("distressed_count", getattr(instance, "distressed_count", 0))
        super().__init__(*args, initial=initial, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500")

    def save(self):
        if not self.instance:
            from .models import DashboardSettings

            self.instance = DashboardSettings.get_solo()
        manager_count_label = self.cleaned_data.get("manager_count_label")
        pension_funds_label = self.cleaned_data.get("pension_funds_label")
        best_performers = self.cleaned_data.get("best_performers")
        distressed_count = self.cleaned_data.get("distressed_count")

        if manager_count_label != "":
            self.instance.manager_count_label = manager_count_label
        if pension_funds_label != "":
            self.instance.pension_funds_label = pension_funds_label
        if best_performers is not None:
            self.instance.best_performers = best_performers
        if distressed_count is not None:
            self.instance.distressed_count = distressed_count
        self.instance.save()
        return self.instance


class IPSReviewEntryForm(forms.ModelForm):
    class Meta:
        model = IPSReviewEntry
        fields = [
            "fund_name",
            "ic_crm",
            "administrator",
            "admin_crm",
            "member_fin_schedules",
            "financial_review",
            "replacement_ratios",
            "date_data_received",
            "date_sent_to_client",
            "workshop_required",
            "asset_mgr_mandates",
            "status_comments",
        ]
        widgets = {
            "fund_name": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "ic_crm": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "administrator": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "admin_crm": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "member_fin_schedules": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"}),
            "financial_review": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"}),
            "replacement_ratios": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "date_data_received": forms.DateInput(attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "date_sent_to_client": forms.DateInput(attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "workshop_required": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"}),
            "asset_mgr_mandates": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "status_comments": forms.Textarea(attrs={"rows": 5, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
        }


class TenderReferralEntryForm(forms.ModelForm):
    class Meta:
        model = TenderReferralEntry
        fields = [
            "source_section",
            "client_name",
            "business_type",
            "contact_name",
            "email_address",
            "date_requested",
            "date_submitted",
            "status_comments",
        ]
        widgets = {
            "source_section": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "client_name": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "business_type": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "contact_name": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "email_address": forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "date_requested": forms.DateInput(attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "date_submitted": forms.DateInput(attrs={"type": "date", "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
            "status_comments": forms.Textarea(attrs={"rows": 5, "class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}),
        }


class SelfGeneratedTargetForm(forms.ModelForm):
    target_group = forms.ChoiceField(
        choices=[
            ("internal", "Internal Target"),
            ("external", "External Target"),
        ],
        widget=forms.Select(
            attrs={"class": "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500"}
        ),
    )

    class Meta:
        model = SelfGeneratedTarget
        fields = [
            "client_name",
            "administrator",
            "business_target",
            "fund_size_usd_m",
            "contact_name",
            "email_address",
            "date_requested",
            "date_submitted",
            "comments",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-teal-500",
            )
        if self.instance and self.instance.pk:
            self.fields["target_group"].initial = (
                "internal" if (self.instance.source_section or "").strip() == "Internal Targets" else "external"
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        target_group = self.cleaned_data.get("target_group")
        obj.source_section = (
            "Internal Targets" if target_group == "internal" else "External Targets (Old Mutual Pipeline)"
        )
        if commit:
            obj.save()
        return obj
