from django import forms

from .models import ClientReport, StatusPhase


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
