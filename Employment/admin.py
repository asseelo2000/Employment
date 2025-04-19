from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import User, Group
import requests  # Import User and Group models

from Employment.forms import  ApplicantEvaluationAdminForm, InterviewAdminForm, JobOfferAdminForm, OnboardingForm, PreEmploymentTestForm
from .models import (
    InterviewStage, Issue, JobApplicationStatus, JobOfferStatus, JobOpening, Applicant, Department, Branch, JobApplication,
    RecruitmentCampaign, PreEmploymentTest, Interview, ApplicantEvaluation,
    JobOffer, Onboarding, ApplicantTracking, TestResult, Feedback
)

from django.contrib import admin, messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User, Group

from django.http import JsonResponse
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Exists, OuterRef
from helpdesk.models import Ticket
# Custom AdminSite to control the order of models
class MyAdminSite(admin.AdminSite):
    site_header = 'Recruitment Admin'
    site_title = 'Recruitment Admin Portal'
    index_title = 'Welcome to the Recruitment Admin Portal'

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)

        # The order in which models should appear
        model_order = [
            'User', 'Group',
            'Department', 'Branch','JobOpening', 'Applicant', 'JobApplication',
            'RecruitmentCampaign', 'PreEmploymentTest', 'Interview',
            'ApplicantEvaluation', 'JobOffer', 'Onboarding', 'ApplicantTracking', 'Feedback', 'Issue'
        ]

        for app_name, app in app_dict.items():
            models = app['models']
            # Create a dict of models
            model_dict = {model['object_name']: model for model in models}
            # Reorder models
            ordered_models = []
            for model_name in model_order:
                if model_name in model_dict:
                    ordered_models.append(model_dict[model_name])
            # Add any models not in model_order at the end
            for model in models:
                if model['object_name'] not in model_dict:
                    ordered_models.append(model)
            app['models'] = ordered_models
        return list(app_dict.values())
    
admin_site = MyAdminSite(name='myadmin')

# Register the User and Group models with the custom admin site
admin_site.register(User, admin.ModelAdmin)

@admin.register(Feedback, site=admin_site)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'message', 'ticket_status', 'received_at', 'sent_by')
    list_filter = ('ticket_status', 'received_at', 'sent_by')
    search_fields = ('ticket__title', 'message', 'sent_by__username')
    date_hierarchy = 'received_at'
    ordering = ('-received_at',)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.groups.filter(name='Supervisors').exists() and not request.user.is_superuser:
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        if not request.user.groups.filter(name='Supervisors').exists() and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

@admin.register(Issue, site=admin_site)
class IssueAdmin(admin.ModelAdmin):
        list_display = ('title', 'user', 'status', 'created_at', 'updated_at')
        list_filter = ('status', 'created_at', 'updated_at')
        search_fields = ('title', 'description', 'user__username')
        readonly_fields = ('created_at', 'updated_at')
        fieldsets = (
            (None, {
                'fields': ('title', 'description', 'attachment', 'origin_url', 'user', 'status', 'ticket')
            }),
        )

        def get_queryset(self, request):
            qs = super().get_queryset(request)
            if request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser:
                return qs
            return qs.filter(user=request.user)

        def save_model(self, request, obj, form, change):
            if not change:
                obj.status = 'sent'
            super().save_model(request, obj, form, change)

        def has_change_permission(self, request, obj=None):
            if obj is None:
                return True
            if request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser:
                return True
            return obj and obj.user == request.user and obj.status == 'sent'

        def has_delete_permission(self, request, obj=None):
            return request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser

# @admin.register(Issue, site=admin_site)
# class IssueAdmin(admin.ModelAdmin):
#     list_display = ('title', 'user', 'status', 'supervisor', 'submitted_at', 'ticket_id')
#     list_filter = ('status', 'supervisor', 'submitted_at')
#     search_fields = ('title', 'description', 'user__username')
#     readonly_fields = ('submitted_at', 'ticket_id')  # Prevent editing these
#     fieldsets = (
#         (None, {
#             'fields': ('title', 'description', 'attachment', 'origin_url', 'user')
#         }),
#         ('Review', {
#             'fields': ('status', 'supervisor', 'refusal_reason', 'ticket_id'),
#             'classes': ('collapse',),  # Collapsible section for supervisors
#         }),
#     )
    
#     def support_ticket_status(self, obj):
#         return obj.get_support_ticket_status()
#     support_ticket_status.short_description = 'Support Ticket Status'

#     def get_list_editable(self, request):
#         if request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser:
#             return ['status']
#         return []

#     def get_changelist_instance(self, request):
#         self.list_editable = self.get_list_editable(request)
#         return super().get_changelist_instance(request)

#     def get_fieldsets(self, request, obj=None):
#         fieldsets = super().get_fieldsets(request, obj)
#         if not request.user.groups.filter(name='Supervisors').exists() and not request.user.is_superuser:
#             # Remove the 'Review' section for non-supervisors
#             fieldsets = [fs for fs in fieldsets if fs[0] != 'Review']
#         return fieldsets

#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser:
#             return qs  # Supervisors see all issues
#         return qs.filter(user=request.user)  # Regular users see only their issues

#     def save_model(self, request, obj, form, change):
#             if not change:
#                 supervisor = User.objects.filter(groups__name='Supervisors').first()
#                 if supervisor:
#                     obj.supervisor = supervisor
#                 obj.status = 'pending'
#                 send_mail(
#                     'New Issue Submitted',
#                     f'A new issue "{obj.title}" has been submitted for review.',
#                     settings.DEFAULT_FROM_EMAIL,
#                     [supervisor.email],
#                     fail_silently=True,
#                 )
#             elif change and 'status' in form.changed_data:
#                 if obj.status == 'approved' and not obj.ticket_id:
#                     payload = {
#                         'company_id': 'employment2',
#                         'title': obj.title,
#                         'description': obj.description,
#                         'user_email': obj.user.email,
#                         'user_id': obj.user.id,
#                         'origin_url': obj.origin_url,
#                         'submitted_at': obj.submitted_at.isoformat(),
#                     }
#                     files = {'attachment': obj.attachment.file} if obj.attachment else {}
#                     headers = {
#                         'Authorization': f'Token {settings.SUPPORT_API_KEY}',  # Employment2's token
#                     }
#                     try:
#                         response = requests.post(
#                             settings.SUPPORT_SUBMIT_URL,
#                             data=payload,
#                             files=files,
#                             headers=headers,
#                         )
#                         if response.status_code == 201:
#                             obj.ticket_id = response.json()['ticket_id']
#                             self.message_user(request, f'Issue "{obj.title}" approved and sent to Support.')
#                         else:
#                             self.message_user(request, f'Failed to send issue to Support: {response.text}', level='error')
#                     except requests.RequestException as e:
#                         self.message_user(request, f'Error sending to Support: {str(e)}', level='error')
#                 elif obj.status == 'refused':
#                     send_mail(
#                         'Issue Refused',
#                         f'Your issue "{obj.title}" was refused. Reason: {obj.refusal_reason or "No reason provided"}',
#                         settings.DEFAULT_FROM_EMAIL,
#                         [obj.user.email],
#                         fail_silently=True,
#                     )
#                     self.message_user(request, f'Issue "{obj.title}" refused.')
#             super().save_model(request, obj, form, change)

    # def save_model(self, request, obj, form, change):
    #     # Auto-assign supervisor for new issues
    #     if not change:  # New issue
    #         supervisor = User.objects.filter(groups__name='Supervisors').first()
    #         if supervisor:
    #             obj.supervisor = supervisor
    #         obj.status = 'pending'
    #         send_mail(
    #             'New Issue Submitted',
    #             f'A new issue "{obj.title}" has been submitted for review.',
    #             settings.DEFAULT_FROM_EMAIL,
    #             [supervisor.email],
    #             fail_silently=True,
    #         )
    #     # Handle status change by supervisor
    #     elif change and 'status' in form.changed_data:
    #         if obj.status == 'approved' and not obj.ticket_id:
    #             # Send to Support
    #             payload = {
    #                 'company_id': 'employment2',  # Hardcoded for Employment2
    #                 'title': obj.title,
    #                 'description': obj.description,
    #                 'user_email': obj.user.email,
    #                 'user_id': obj.user.id,
    #                 'origin_url': obj.origin_url,
    #                 'submitted_at': obj.submitted_at.isoformat(),
    #             }
    #             files = {'attachment': obj.attachment.file} if obj.attachment else {}
    #             try:
    #                 response = requests.post(
    #                     'http://127.0.0.1:8001/api/submit-ticket/',
    #                     data=payload,
    #                     files=files,
    #                 )
    #                 if response.status_code == 201:
    #                     obj.ticket_id = response.json()['ticket_id']
    #                     self.message_user(request, f'Issue "{obj.title}" approved and sent to Support.')
    #                 else:
    #                     self.message_user(request, f'Failed to send issue to Support: {response.text}', level='error')
    #             except requests.RequestException as e:
    #                 self.message_user(request, f'Error sending to Support: {str(e)}', level='error')
    #         elif obj.status == 'refused':
    #             send_mail(
    #                 'Issue Refused',
    #                 f'Your issue "{obj.title}" was refused. Reason: {obj.refusal_reason or "No reason provided"}',
    #                 settings.DEFAULT_FROM_EMAIL,
    #                 [obj.user.email],
    #                 fail_silently=True,
    #             )
    #             self.message_user(request, f'Issue "{obj.title}" refused.')
    #     super().save_model(request, obj, form, change)

    # def has_change_permission(self, request, obj=None):
    #     if obj is None:  # List view
    #         return True
    #     if request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser:
    #         return True  # Supervisors can edit anything
    #     return obj and obj.user == request.user and obj.status == 'pending'  # Users can edit their own pending issues

    # def has_delete_permission(self, request, obj=None):
    #     return request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser
    
@admin.register(Group, site=admin_site)
class Group( admin.ModelAdmin):
    list_display= ("name", "user__username")
# Register each model with full ModelAdmin options

@admin.register(Branch, site=admin_site)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_name', 'user', 'phone', 'type', 'status', 'is_deleted')
    list_filter = ('type', 'status', 'is_deleted')
    search_fields = ('branch_name', 'user__username', 'user__first_name', 'user__last_name', 'phone')
    ordering = ('branch_name',)
    # raw_id_fields = ('user',)

    # Custom method to display the user's username
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    # Override the form field for the organizer to filter users
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "user":
    #         alrasheed_admins_group  = Group.objects.get(name="alrasheed_admins")
    #         kwargs["queryset"] = User.objects.filter(groups=alrasheed_admins_group )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)


# #_______________________Custom Actions Start_______________________________#
def send_application_received_email(modeladmin, request, queryset):
    """
    Admin action to send an email notification to applicants informing them
    that their job application has been received.
    """
    for application in queryset:
        try:
            user = application.applicant.user  # Assuming Applicant has a OneToOneField to User
            subject = f"Application Received for {application.job_opening.title}"
            
            # Render HTML and plain text versions of the email
            html_message = render_to_string('emails/application_received.html', {'application': application})
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=[user.username],
                html_message=html_message,
                fail_silently=False,
            )
            modeladmin.message_user(request, f"Email sent to {user.username}", messages.SUCCESS)
        except Exception as e:
            modeladmin.message_user(request, f"Failed to send email to {application.applicant.user.email}: {str(e)}", messages.ERROR)

send_application_received_email.short_description = "Send application received email to selected applicants"
# # _______________________Custom Actions End_______________________________#

@admin.register(Department, site=admin_site)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head', 'is_active', 'is_deleted')
    list_filter = ('is_active', 'is_deleted')
    search_fields = ('name', 'description', 'head__username', 'head__first_name', 'head__last_name')
    ordering = ('name',)
    # raw_id_fields = ('head',)
    
@admin.register(JobOpening, site=admin_site)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'branch', 'status', 'is_active', 'posted_date', 'closing_date')
    list_filter = ('status', 'is_active', 'department', 'branch', 'work_schedule_type')
    search_fields = ('title', 'description', 'requirements')
    ordering = ('-posted_date',)
    date_hierarchy = 'posted_date'
    list_editable = ('status', 'is_active')
    list_per_page = 25
    # raw_id_fields = ('department', 'branch')

@admin.register(Applicant, site=admin_site)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'first_name', 'last_name', 'phone', 'gender', 'date_of_birth', 'is_deleted')
    list_filter = ('gender', 'is_deleted')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'address')
    ordering = ('user__username',)
    date_hierarchy = 'created_at'
    # raw_id_fields = ('user',)
    list_per_page = 25


    # Make the model read-only
    def has_add_permission(self, request):
        return False  # Prevent adding new Applicants

@admin.register(JobApplication, site=admin_site)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('id','applicant__user', 'job_opening', 'branch', 'status', 'applied_date', 'is_deleted')
    list_filter = ('status', 'application_platform', 'is_deleted')
    search_fields = (
        'applicant__user__username', 'applicant__user__first_name', 'applicant__user__last_name',
        'job_opening__title'
    )
    date_hierarchy = 'applied_date'
    # raw_id_fields = ('applicant', 'branch', 'job_opening')
    list_editable = ('status',)
    ordering = ('-applied_date',)
    readonly_fields = "get_readonly_fields", 
    actions = [send_application_received_email]


    # make all jobapplications fields read-only except the status field
    def get_readonly_fields(self, request, obj=None):
        if obj:  # If the object already exists
            # Make all fields read-only except 'editable_field_name'
            return [field.name for field in self.model._meta.fields if field.name != 'status']
        return self.readonly_fields  # If it's a new object, return the default
    
    # Make the model read-only
    def has_add_permission(self, request):
        return False  # Prevent adding new JobApplications
    
    # def has_change_permission(self, request, obj=None):
    #     # Prevent changing permissions
    #     if request.user.has_perm('auth.change_permission'):
    #         return False
    #     return super().has_change_permission(request, obj)  # Prevent admin from changing JobApplications

@admin.register(RecruitmentCampaign, site=admin_site)
class RecruitmentCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign_type', 'start_date', 'end_date', 'organizer', 'is_active', 'is_deleted')
    list_filter = ('campaign_type', 'is_active', 'is_deleted')
    search_fields = ('name', 'description', 'organizer__username', 'organizer__first_name', 'organizer__last_name')
    date_hierarchy = 'start_date'
    # raw_id_fields = ('organizer',)
    filter_horizontal = ('job_openings',)
    ordering = ('-start_date',)

# Optional: A method to customize how the organizer is displayed
    def organizer_username(self, obj):
        return obj.organizer.username if obj.organizer else "No Organizer"
    organizer_username.short_description = 'Organizer Username'

    # Override the form field for the organizer to filter users
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "organizer":
    #         organizers_group = Group.objects.get(name="organizers")
    #         kwargs["queryset"] = User.objects.filter(groups=organizers_group)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(PreEmploymentTest, site=admin_site)
class PreEmploymentTestAdmin(admin.ModelAdmin):
    form = PreEmploymentTestForm

    list_display = (
        'applicant', 'job_opening', 'test_type', 'score', 
        'duration', 'test_date', 'result', 'evaluator',
    )
    list_filter = ('test_type', 'result',  'test_date')
    list_editable = ('result',)
    search_fields = (
        'applicant__user__username', 'applicant__user__first_name', 'applicant__user__last_name',
        'job_opening__title',  'evaluator_username'
    )
    date_hierarchy = 'test_date'
    ordering = ('-test_date',)

    # Optional: A method to customize how the organizer is displayed
    def evaluator_username(self, obj):
        return obj.evaluator.username if obj.evaluator else "No Evaluator"
    evaluator_username.short_description = 'Evaluator Username'
    

    # displaying applicants who have the shortlisted status in the jobapplication
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "applicant":
    #         shortlisted_applicants = Applicant.objects.filter(
    #             job_applications__status=JobApplicationStatus.SHORTLISTED,
    #         ).distinct()
    #         kwargs["queryset"] = shortlisted_applicants
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Override the form field for the evaluator to filter users
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "evaluator":
    #         evaluators_group  = Group.objects.get(name="evaluators")
    #         kwargs["queryset"] = User.objects.filter(groups=evaluators_group )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(Interview, site=admin_site)
class InterviewAdmin(admin.ModelAdmin):
    form = InterviewAdminForm

    list_display = ('applicant', 'job_opening', 'interview_date', 'interview_stage', 'is_deleted')
    list_filter = ('interview_stage', 'interview_mode', 'is_deleted')
    list_editable = ("interview_stage",)
    search_fields = (
        'applicant__user__username', 'applicant__user__first_name', 'applicant__user__last_name',
        'job_opening__title'
    )
    date_hierarchy = 'interview_date'
    # raw_id_fields = ('applicant', 'job_opening')
    filter_horizontal = ('interviewers',)
    ordering = ('-interview_date',)

    # Customizing form field behavior for applicant to limit choices
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "applicant":
    #         kwargs["queryset"] = Applicant.objects.filter(
    #             pre_employment_tests__result=TestResult.PASS
    #         ).distinct()
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

#     # Customizing form field behavior for interviewers
    # def formfield_for_manytomany(self, db_field, request, **kwargs):
    #     if db_field.name == "interviewers":
    #         interviewers_group = Group.objects.get(name="interviewers")
    #         kwargs["queryset"] = User.objects.filter(groups=interviewers_group)
    #     return super().formfield_for_manytomany(db_field, request, **kwargs)

@admin.register(ApplicantEvaluation, site=admin_site)
class ApplicantEvaluationAdmin(admin.ModelAdmin):
    form = ApplicantEvaluationAdminForm

    list_display = ('applicant', 'job_opening', 'overall_score','evaluator', 'evaluation_date', 'is_final')
    list_filter = ('is_final','overall_score')
    search_fields = (
        'applicant__user__username', 'applicant__user__first_name', 'applicant__user__last_name',
        'job_opening__title'
    )
    date_hierarchy = 'evaluation_date'
    ordering = ('-evaluation_date',)

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "applicant":
    #         kwargs["queryset"] = Applicant.objects.filter(
    #             interviews_applicant__interview_stage= InterviewStage.FINAL
    #         )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
        

    # Override the form field for the evaluator to filter users
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "evaluator":
    #         evaluators_group  = Group.objects.get(name="evaluators")
    #         kwargs["queryset"] = User.objects.filter(groups=evaluators_group)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(JobOffer, site=admin_site)
class JobOfferAdmin(admin.ModelAdmin):
    form = JobOfferAdminForm

    list_display = ('id','title','applicant__first_name', 'job_opening', 'offer_date', 'status', 'salary_offered', 'is_deleted')
    list_filter = ('status', 'is_deleted')
    search_fields = ('title', 'applicant__user__username', 'applicant__user__first_name', 'applicant__user__last_name',
        'job_opening__title'
    )
    date_hierarchy = 'offer_date'
    # raw_id_fields = ('applicant', 'job_opening')
    ordering = ('-offer_date',)
    list_editable = ('status',)

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "applicant":
    #         kwargs["queryset"] = Applicant.objects.filter(
    #             evaluations__is_final= True
    #         )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(Onboarding, site=admin_site)
class OnboardingAdmin(admin.ModelAdmin):
    # form = OnboardingForm

    list_display = ('job_offer__title', 'employee', 'job_opening', 'hiring_date', 'status', 'contract_signed', 'onboarding_completion')
    list_filter = ('status', 'contract_signed', 'onboarding_completion')
    list_editable = ("status",)
    search_fields = (
        'employee__user__username', 'employee__first_name', 'employee__last_name',
        'job_opening__title', 'job_offer__title'
    )
    date_hierarchy = 'hiring_date'
    # raw_id_fields = ('employee', 'job_opening', 'job_offer', 'assigned_mentor')
    ordering = ('-hiring_date',)
    autocomplete_fields = ['job_offer']
    
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "job_offer":
    #         kwargs["queryset"] = Applicant.objects.filter(
    #             job_offers_applicants__status= JobOfferStatus.ACCEPTED
    #         )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(ApplicantTracking, site=admin_site)
class ApplicantTrackingAdmin(admin.ModelAdmin):
    list_display = ('id','applicant', 'job_opening','stage', 'application_status', 'tracking_date', 'is_deleted')
    list_filter = ('application_status', 'is_deleted')
    search_fields = (
        'applicant__user__username', 'applicant__user__first_name', 'applicant__user__last_name',
        'job_opening__title'
    )
    date_hierarchy = 'tracking_date'
    # raw_id_fields = ('applicant', 'job_opening')
    ordering = ('-tracking_date',)



















# from django.contrib import admin, messages
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags

# from django.contrib.auth.models import User, Group
# from Employment.forms import ApplicantAdminForm,  PreEmploymentTestForm
# from .models import Branch, Department, Interview, JobApplication, JobApplicationStatus, JobOpening, Applicant, PreEmploymentTest, RecruitmentCampaign, TestResult



# @admin.register(Branch)
# class BranchAdmin(admin.ModelAdmin):
#     list_display = ('branch_name', 'user_username', 'phone', 'type', 'status')
#     list_filter = ('type', 'status')
#     search_fields = ('user__username', 'branch_name', 'phone')
#     list_editable = ('phone', 'status')
#     ordering = ('branch_name',)


# @admin.register(JobOpening)
# class JobOpeningAdmin(admin.ModelAdmin):
#     list_display = ('id','title','posted_date','closing_date','is_active',)
#     list_filter = ('posted_date', 'closing_date', 'requirements', 'branch__branch_name')
#     search_fields = ('title', 'branch__branch_name', 'description', 'requirements', 'location')
#     list_editable = ('title', 'closing_date')
#     date_hierarchy = 'posted_date'
#     ordering = ('-posted_date',)

# @admin.register(Applicant)
# class ApplicantAdmin(admin.ModelAdmin):
#     form = ApplicantAdminForm

#     list_display = ('user_first_name', 'user_last_name','user', 'phone', 'gender')
#     list_filter = ('gender',)
#     search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
#     # list_editable = ('phone', 'gender', 'type')
#     date_hierarchy = 'user__date_joined'
#     ordering = ('user__first_name',)

# @admin.register(JobApplication)
# class JobApplicationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'applicant', 'job_opening', 'branch', 'applied_date', 'status')
#     list_filter = ('applied_date',)
#     search_fields = ('applicant__user__username', 'job_opening__title', 'branch')
#     date_hierarchy = 'applied_date'
#     list_editable = ('status',)
#     ordering = ('-applied_date',)


    
# @admin.register(RecruitmentCampaign)
# class RecruitmentCampaignAdmin(admin.ModelAdmin):
#     list_display = ('name', 'start_date', 'end_date', 'organizer_username', 'attendees_count', 'is_active')
#     list_filter = ('start_date', 'end_date', 'is_active')
#     search_fields = ('name', 'description', 'organizer__username')
#     filter_horizontal = ('job_openings',)  # For better selection of ManyToManyField
#     date_hierarchy = 'start_date'
#     ordering = ('-start_date',)

#     # Custom method to make the model read-only for specific fields, if necessary
#     # readonly_fields = ('attendees_count',)

#     
    

# @admin.register(Department)
# class BDepartmentAdmin(admin.ModelAdmin):
#     list_display= ('name',)

# class PreEmploymentTestAdmin(admin.ModelAdmin):
#     form = PreEmploymentTestForm

#     list_display = (
#         'applicant', 'job_opening', 'test_type', 'score', 
#         'duration', 'test_date', 'result', 'evaluator'
#     )
#     list_filter = ('test_type', 'result', 'test_date')
#     search_fields = ('applicant__user__username', 'job_opening__title', 'evaluator__username')
#     date_hierarchy = 'test_date'
#     ordering = ('-test_date',)



# # Restrict the job_opening field based on the selected applicant
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == "job_opening":
#             # Check if 'applicant' is provided in the request
#             if 'applicant' in request.GET:
#                 try:
#                     applicant_id = int(request.GET.get('applicant'))
#                     # Filter JobOpening objects to only those that have a related JobApplication with this applicant
#                     job_application_ids = JobApplication.objects.filter(
#                         applicant_id=applicant_id
#                     ).values_list('job_opening_id', flat=True)
#                     kwargs["queryset"] = JobOpening.objects.filter(id__in=job_application_ids)
#                 except (ValueError, TypeError):
#                     pass

#         return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    
# admin.site.register(PreEmploymentTest, PreEmploymentTestAdmin)


# @admin.register(Interview)
# class InterviewAdmin(admin.ModelAdmin):

#     list_display = (
#         'applicant', 'job_opening', 'interview_date', 'interview_mode',
#         'interview_stage', 'is_deleted', 'created_at', 'updated_at'
#     )
#     list_filter = ('interview_date', 'interview_mode', 'interview_stage', 'is_deleted')
#     search_fields = (
#         'applicant__user__username', 'applicant__user__first_name', 
#         'applicant__user__last_name', 'job_opening__title', 'interview_address'
#     )
#     filter_horizontal = ('interviewers',)  # For ManyToManyField selection
#     date_hierarchy = 'interview_date'
#     ordering = ('-interview_date',)
#     # Making 'job_opening' field read-only as it should not be editable
#     # readonly_fields = ('job_opening',)


# 



