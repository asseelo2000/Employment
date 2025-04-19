from django import forms
from .models import *
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_select2.forms import ModelSelect2Widget
from helpdesk.forms import PublicTicketForm  # Adjust the import path as necessary
from django_select2 import forms as s2forms
from .models import Interview

class CustomPublicTicketForm(PublicTicketForm):
    url = forms.CharField(
        max_length=255,
        required=False,
        label="URL of the Issue",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="The page where you encountered this issue."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'body' in self.fields:
            self.fields['description'] = self.fields.pop('body')
            self.fields['description'].label = "Issue Description"
        self.order_fields(['title', 'description', 'url', 'submitter_email', 'priority', 'due_date', 'queue'])

    def save(self, user):
        # Create the ticket using the parent save method
        ticket = super().save(user)
        # Set the url field directly on the ticket
        ticket.url = self.cleaned_data.get('url', '')
        ticket.save()
        return ticket

class JobOfferWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "title__icontains",  # Adjust 'title' to the appropriate field in JobOffer
    ]


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = Onboarding
        fields = "__all__"
        widgets = {
            "job_offer": JobOfferWidget,
            # ... other widgets
        }


class ApplicantAdminForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the user queryset to only include users who are already linked to an Applicant
        self.fields["user"].queryset = User.objects.filter(applicant__isnull=False)


# Custom form for handling duration in minutes
class PreEmploymentTestForm(forms.ModelForm):

    class Meta:
        model = PreEmploymentTest
        fields = "__all__"

    duration_in_minutes = forms.IntegerField(
        required=False,
        label="Duration (Minutes)",
        help_text="Enter the duration in minutes.",
    )

    def clean(self):
        cleaned_data = super().clean()
        applicant = cleaned_data.get("applicant")
        job_opening = cleaned_data.get("job_opening")

        if (
            job_opening
            and not JobApplication.objects.filter(
                applicant=applicant, job_opening=job_opening
            ).exists()
        ):
            raise forms.ValidationError(
                "Selected job opening is not applied for by the selected applicant."
            )

        duration_in_minutes = cleaned_data.get("duration_in_minutes")
        if duration_in_minutes is not None:
            cleaned_data["duration"] = timedelta(minutes=duration_in_minutes)

        return cleaned_data


class InterviewAdminForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = "__all__"
        field_order = [
            "applicant",
            "job_opening",
            "interview_date",
            "interview_mode",
            "interview_address",
            "interview_location",
            "interview_stage",
            "interviewers",
            "feedback",
            "is_deleted",
        ]


class ApplicantEvaluationAdminForm(forms.ModelForm):
    class Meta:
        model = ApplicantEvaluation
        fields = "__all__"
        field_order = [
            "applicant",
            "job_opening",
            "skills_score",
            "experience_score",
            "interview_score",
            "overall_score",
            "comments",
            "evaluation_date",
            "evaluator",
            "is_final",
        ]

    def clean(self):
        cleaned_data = super().clean()
        applicant = cleaned_data.get("applicant")
        job_opening = cleaned_data.get("job_opening")

        if (
            job_opening
            and not JobApplication.objects.filter(
                applicant=applicant, job_opening=job_opening
            ).exists()
        ):
            raise forms.ValidationError(
                _("Selected job opening is not applied for by the selected applicant.")
            )

        return cleaned_data


class JobOfferAdminForm(forms.ModelForm):
    class Meta:
        model = JobOffer
        fields = "__all__"
        widgets = {
            "applicant": ModelSelect2Widget(
                search_fields=["first_name__icontains"],
                dependent_fields={
                    # "grade_category": "grade_categories",
                },
                attrs={"class": "select2"},
            ),
            "job_opening": ModelSelect2Widget(
                search_fields=["title__icontains"],
                dependent_fields={
                    "applicant": "applications",
                },
                attrs={"class": "select2"},
            ),
        }
        field_order = [
            "applicant",
            "job_opening",
            "offer_date",
            "offer_expiry_date",
            "position_start_date",
            "salary_offered",
            "benefits",
            "status",
            "negotiation_notes",
            "final_salary",
            "is_deleted",
        ]

    def clean(self):
        cleaned_data = super().clean()
        applicant = cleaned_data.get("applicant")
        job_opening = cleaned_data.get("job_opening")

        if (
            job_opening
            and not JobApplication.objects.filter(
                applicant=applicant, job_opening=job_opening
            ).exists()
        ):
            raise ValidationError(
                _("Selected job opening is not applied for by the selected applicant.")
            )

        return cleaned_data


class OnboardingAdminForm(forms.ModelForm):
    class Meta:
        model = Onboarding
        fields = "__all__"
        field_order = [
            "job_offer",
            "employee",
            "job_opening",
            "hiring_date",
            "contract_signed",
            "onboarding_completion",
            "orientation_date",
            "assigned_mentor",
            "training_schedule",
            "documents_submitted",
            "status",
            "is_deleted",
        ]

    def clean(self):
        cleaned_data = super().clean()
        job_offer = cleaned_data.get("job_offer")
        employee = cleaned_data.get("employee")
        job_opening = cleaned_data.get("job_opening")

        if job_offer:
            if employee != job_offer.applicant:
                raise ValidationError(
                    _(
                        "Selected employee does not match the applicant in the Job Offer."
                    )
                )
            if job_opening != job_offer.job_opening:
                raise ValidationError(
                    _(
                        "Selected job opening does not match the Job Opening in the Job Offer."
                    )
                )

        return cleaned_data


# class JobOpeningWidget(ModelSelect2Widget):
#     model = JobOpening
#     search_fields = ["title__icontains"]
#     forward = ["job_offer"]

#     def get_url(self):
#         return reverse_lazy("jobopening_autocomplete")


