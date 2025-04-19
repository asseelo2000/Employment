from datetime import timezone
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from location_field.models.plain import PlainLocationField 
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
import requests
from smart_selects.db_fields import ChainedForeignKey
from django.db.models import Q
from helpdesk.models import Ticket

from Employment.utils.filters import filter_accepted_job_offers, filter_alrasheed_admins, filter_evaluators, filter_final_evaluations, filter_final_interview_stage, filter_interviewers, filter_mentors, filter_organizers
from django.contrib.auth.models import Group


#______________________Branch Model class Start_____________________#
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Department Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments', verbose_name=_("Department Head"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return self.name
    
class Branch(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="branch_users",
        limit_choices_to = filter_alrasheed_admins
    )
    branch_name = models.CharField(max_length=100, verbose_name=_("Branch Name"))
    phone = models.CharField(max_length=9, verbose_name=_("Phone Number"))
    image = models.ImageField(upload_to="branches/images/", blank=True, null=True, verbose_name=_("Branch Image"))
    type = models.CharField(
        max_length=15,
        choices=[('English Section', 'English Section'), ('Arabic Section', 'Arabic Section')],
        default='Arabic',
        verbose_name=_("Branch Type")
    )
    status = models.CharField(
        max_length=15,
        choices=[('Employing', 'Employing'), ('Not Employing', 'Not Employing')],
        default='Employing',
        verbose_name=_("Employment Status")
    )
    branch_address = models.CharField(max_length=150, default='مدرسة الرشيد شارع الرباط صنعاء',  verbose_name=_("Branch Address"))
    branch_location = PlainLocationField(based_fields=["branch_address"], zoom=14, default="branch_address", verbose_name=_("Branch Location"))
    # manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_branches', verbose_name=_("Branch Manager"))
    created_at = models.DateTimeField(verbose_name=("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"), auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return f"{self.branch_name}"
        # return f"{self.branch_name} - {self.user.get_full_name() or self.user.username}"

#______________________Branch Model class End_____________________#

#______________________JobOpening Model classes Start_____________________#
class JobOpeningStatus(models.TextChoices):
    OPEN = 'Open', _('Open')
    CLOSED = 'Closed', _('Closed')
    ON_HOLD = 'On Hold', _('On Hold')

class JobOpening(models.Model):
    # job_code = models.CharField(max_length=50, unique=True, verbose_name=_("Job Code"))
    title = models.CharField(max_length=255, verbose_name=_("Job Title"))
    description = models.TextField(default='يشبسيبسيبسيبيسبسيببيسب', verbose_name=_("Job Description"))
    requirements = models.TextField(default='يشبسيبسيبسيبيسبسيببيسب', verbose_name=_("Job Requirements"))
    work_schedule_type = models.CharField(
        _("Schedule Type"),
        max_length=15,
        choices=[('Full-time', 'Full-time'), ('Part-time', 'Part-time')]
    )
    salary_range = models.CharField(max_length=100, verbose_name=_("Salary Range"))
    department = models.ForeignKey('Department', related_name='job_openings', on_delete=models.CASCADE, verbose_name=_("Department"))
    posted_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Posted Date"))
    closing_date = models.DateTimeField(verbose_name=_("Closing Date"))
    branch = models.ForeignKey("Branch", related_name="job_openings", on_delete=models.CASCADE, verbose_name=_("Opening Branch"))
    status = models.CharField(
        _("Job Status"),
        max_length=15,
        choices=JobOpeningStatus.choices,
        default=JobOpeningStatus.OPEN
    )
    is_active = models.BooleanField(verbose_name=_("Is Available"), default=True)
    created_at = models.DateTimeField(verbose_name=("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"), auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return f"{self.title}"
        # return f"{self.title} - {self.status}"

    def save(self, *args, **kwargs):
        """
        Override the save method to automatically set is_active
        based on the job status.
        """
        # Mapping status to is_active
        status_to_active_map = {
            JobOpeningStatus.CLOSED: False,
            JobOpeningStatus.ON_HOLD: False,
        }
        # Determine is_active based on the status, default to True
        self.is_active = status_to_active_map.get(self.status, True)

        super().save(*args, **kwargs)

#______________________JobOpening Model classes End_____________________#

#______________________Applicant Model class Start_____________________#
class Applicant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applicants")
    first_name = models.CharField(verbose_name=_("First Name"), max_length=50, blank=True)
    last_name = models.CharField(verbose_name=_("Last Name"), max_length=50, blank=True)
    phone = models.CharField(max_length=15, verbose_name=_("Phone Number"))
    image = models.ImageField(upload_to="applicants/images/", blank=True, null=True, verbose_name=_("Profile Image"))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Date of Birth"))
    address = models.TextField(verbose_name=_("Address"))
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        default='Male',
        verbose_name=_("Gender")
    )
    linkedin_profile = models.URLField(blank=True, null=True, verbose_name=_("LinkedIn Profile"))
    resume = models.FileField(upload_to='applicants/resumes/', blank=True, null=True, verbose_name=_("Resume"))
    created_at = models.DateTimeField(verbose_name=("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"), auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
#______________________Applicant Model class End_____________________#

#______________________JobApplication Model classes Start_____________________#
class ApplicationSource(models.TextChoices):
    PORTAL = 'Portal', _('Portal')
    EMAIL = 'Email', _('Email')
    SOCIAL_MEDIA = 'Social Media', _('Social Media')
    IN_PERSON = 'In Person', _('In Person')
    REFERRAL = 'Referral', _('Referral')

class JobApplicationStatus(models.TextChoices):
    RECEIVED = 'Received', _('Received')
    UNDER_REVIEW = 'Under Review', _('Under Review')
    SHORTLISTED = 'Shortlisted', _('Shortlisted')
    REJECTED = 'Rejected', _('Rejected')
    HIRED = 'Hired', _('Hired')

class JobApplication(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='job_applications', verbose_name=("Applied By"))
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="job_applications_branch", verbose_name=("Branch"))
    job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name="applications", verbose_name=("Applied Job"))
    resume = models.FileField(upload_to='applicants/resumes/', verbose_name=_("Resume"))
    cover_letter = models.TextField(blank=True, null=True, verbose_name=_("Cover Letter"))
    applied_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Applied Date"))
    application_platform = models.CharField(
        max_length=50,
        choices=ApplicationSource.choices,
        default=ApplicationSource.PORTAL,
        verbose_name=_("Application Platform")
    )
    status = models.CharField(
        max_length=50,
        choices=JobApplicationStatus.choices,
        default=JobApplicationStatus.RECEIVED,
        verbose_name=_("Application Status")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(verbose_name=("Created At"),auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"),auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    class Meta:
        unique_together = ('applicant', 'job_opening')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['job_opening']),
        ]

    def __str__(self):
        return f"{self.applicant.user.get_full_name()} - {self.job_opening.title}"

    # for updating the ApplicantTracking with changes
    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            ApplicantTracking.objects.create(
                applicant=self.applicant,
                job_opening=self.job_opening,
                stage="Application",
                application_status=self.status,
                notes="Job application updated."
            )
#______________________JobApplication classes End_____________________#

#______________________RecruitmentCampaign Model classes Start_____________________#
class CampaignType(models.TextChoices):
    JOB_FAIR = 'Job Fair', _('Job Fair')
    ONLINE_ADS = 'Online Ads', _('Online Ads')
    REFERRAL = 'Referral', _('Referral')
    CAMPUS_RECRUITMENT = 'Campus Recruitment', _('Campus Recruitment')

class RecruitmentCampaign(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Campaign Name"))
    description = models.TextField(verbose_name=_("Campaign Description"))
    campaign_type = models.CharField(
        max_length=50,
        choices=CampaignType.choices,
        default=CampaignType.ONLINE_ADS,
        verbose_name=_("Campaign Type")
    )
    target_audience = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Target Audience"))
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Budget"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))

    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Organizer"),
        limit_choices_to=filter_organizers
        )
    
    job_openings = models.ManyToManyField(
        JobOpening,
        related_name='campaign_job_openings',
        limit_choices_to={'status': JobOpeningStatus.OPEN, 'is_active': True},
        verbose_name=_("Job Openings")
    )
    attendees_count = models.IntegerField(default=0, verbose_name=_("Expected Attendees"))
    campaign_address = models.CharField(max_length=255, default='Sanaa', verbose_name=_("Campaign Address"))
    location = PlainLocationField(based_fields=["campaign_address"], zoom=14, default='', verbose_name=_("Location"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(verbose_name=("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"), auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return self.name
#______________________RecruitmentCampaign Model classes End_____________________#

#______________________PreEmploymentTest Model classes Start_____________________#
class TestResult(models.TextChoices):
    PASS = 'Pass', _('Pass')
    FAIL = 'Fail', _('Fail')
    PENDING = 'Pending', _('Pending')

class PreEmploymentTest(models.Model):
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='pre_employment_tests',
        limit_choices_to={'job_applications__status': JobApplicationStatus.SHORTLISTED},
        verbose_name=_("Applicant")
    )
    job_opening = ChainedForeignKey(
        JobOpening,
        chained_field="applicant",
        chained_model_field="applications__applicant",
        show_all=False,
        auto_choose=True,
        sort=True,
        related_name='pre_employment_tests',
        verbose_name=_("Job Opening")
    )
    test_type = models.CharField(
        max_length=50,
        choices=[('Technical', 'Technical'), ('Personality', 'Personality'), ('Group', 'Group')],
        default='Technical',
        verbose_name=_("Test Type")
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_("Score"),
        help_text="max score is 10"
    )
    duration = models.DurationField(blank=True, null=True, verbose_name=_("Duration"))
    test_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Test Date"))
    result = models.CharField(
        max_length=50,
        choices=TestResult.choices,
        default=TestResult.PENDING,
        verbose_name=_("Test Result")
    )
    test_link = models.URLField(blank=True, null=True, verbose_name=_("Test Link"))
    evaluator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Evaluator"),
        limit_choices_to = filter_evaluators

        )

    def save(self, *args, **kwargs):
        if self.score >= 5.0:
            self.result = TestResult.PASS
        else:
            self.result = TestResult.FAIL
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Determine test result based on score
        if self.score >= 5.0:
            self.result = TestResult.PASS
        else:
            self.result = TestResult.FAIL

        # Call the parent save method
        super().save(*args, **kwargs)

        # Log this test in ApplicantTracking
        ApplicantTracking.objects.create(
            applicant=self.applicant,
            job_opening=self.job_opening,
            stage="Pre-Employment Test",
            application_status="Test Result Recorded",
            notes=f"Test Type: {self.test_type}, Score: {self.score}, Result: {self.result}"
        )
#______________________PreEmploymentTest Model classes End_____________________#

#______________________Interview Model classes Start_____________________#
class InterviewStage(models.TextChoices):
    PHONE_SCREEN = 'Phone Screen', _('Phone Screen')
    TECHNICAL = 'Technical Interview', _('Technical Interview')
    HR = 'HR Interview', _('HR Interview')
    FINAL = 'Final Interview', _('Final Interview')

class Interview(models.Model):
    title = models.CharField(max_length=200)
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='interviews_applicant',
        limit_choices_to={
            'pre_employment_tests__result': TestResult.PASS
        },
        verbose_name=_("Applicant")
    )
    job_opening = ChainedForeignKey(
        JobOpening,
        chained_field="applicant",
        chained_model_field="applications__applicant",
        show_all=False,
        auto_choose=False,
        sort=True,
        verbose_name=_("Job Opening"),
        related_name="interview_jobopining"
    )
    interview_date = models.DateTimeField(verbose_name=_("Interview Date"))
    interview_mode = models.CharField(
        max_length=50,
        choices=[('Online', 'Online'), ('In Person', 'In Person')],
        default='In Person',
        verbose_name=_("Interview Mode")
    )
    interview_address = models.CharField(max_length=255, default='Sanaa', verbose_name=_("Interview Address"))
    interview_location = PlainLocationField(based_fields=["interview_address"], zoom=14, default='', verbose_name=_("Interview Location"))
    interview_stage = models.CharField(
        max_length=50,
        choices=InterviewStage.choices,
        default=InterviewStage.PHONE_SCREEN,
        verbose_name=_("Interview Stage")
    )
    interviewers = models.ManyToManyField(
        User,
        related_name='interviews',
        verbose_name=_("Interviewers"),
        limit_choices_to = filter_interviewers
        )
    feedback = models.TextField(blank=True, null=True, verbose_name=_("Feedback"))
    created_at = models.DateTimeField(verbose_name=("Created At"),auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"),auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            ApplicantTracking.objects.create(
                applicant=self.applicant,
                job_opening=self.job_opening,
                stage="Interview",
                application_status="Interview Scheduled",
                notes=f"Interview scheduled for stage: {self.interview_stage}."
            )
#______________________Interview Model classes End_____________________#

#______________________ApplicantEvaluation Model class Start_____________________#
class ApplicantEvaluation(models.Model):
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_("Applicant"), 
        limit_choices_to = filter_final_interview_stage
    )
    job_opening = ChainedForeignKey(
        JobOpening,
        chained_field="applicant",
        chained_model_field="applications__applicant",
        show_all=False,
        auto_choose=False,
        sort=True,
        verbose_name=_("Job Opening")
    )
    skills_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_("Skills Score"),
        help_text="max score is 10"
    )
    experience_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_("Experience Score"),
        help_text="max score is 10"
    )
    interview_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_("Interview Score"),
        help_text="max score is 10"
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Overall Score"),
        editable=False,
        help_text="max score is 30"
    )
    comments = models.TextField(blank=True, null=True, verbose_name=_("Comments"))
    evaluation_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Evaluation Date"))
    evaluator = models.ForeignKey(
        User,
        related_name='evaluations',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Evaluator"),
        limit_choices_to = filter_evaluators
    )
    
    is_final = models.BooleanField(default=False, verbose_name=_("Is Final Evaluation"))



    def __str__(self):
        return f"Evaluation for {self.applicant.user.get_full_name()} - {self.job_opening.title}"
    
    def save(self, *args, **kwargs):
        # Calculate overall score
        self.overall_score = self.skills_score + self.experience_score + self.interview_score
        
        # Save the current evaluation object
        super().save(*args, **kwargs)

        # Fetch the current job application status for the applicant and job opening
        try:
            job_application = JobApplication.objects.get(
                applicant=self.applicant,
                job_opening=self.job_opening
            )
            application_status = job_application.status
        except JobApplication.DoesNotExist:
            application_status = "Unknown"  # Fallback if no job application is found

        # Log this evaluation in ApplicantTracking
        ApplicantTracking.objects.create(
            applicant=self.applicant,
            job_opening=self.job_opening,
            stage="Evaluation",
            application_status=application_status,
            notes="Evaluation scores updated."
        )
#______________________ApplicantEvaluation Model class End_____________________#


#______________________JobOffer Model classes Start_____________________#
class JobOfferStatus(models.TextChoices):
    PENDING = 'Pending', _('Pending')
    ACCEPTED = 'Accepted', _('Accepted')
    REJECTED = 'Rejected', _('Rejected')

class JobOffer(models.Model):
    title = models.CharField(verbose_name=_("Job Offer Title"), max_length=100)
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='job_offers_applicants',
        verbose_name=_("Applicant"),
        limit_choices_to = filter_final_evaluations
    )
    job_opening = models.ForeignKey(
        JobOpening,
        on_delete=models.CASCADE,
        related_name='job_offers',
        verbose_name=_("Job Opening")
    )
    offer_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Offer Date"))
    offer_expiry_date = models.DateTimeField(verbose_name=_("Offer Expiry Date"))
    position_start_date = models.DateField(verbose_name=_("Position Start Date"))
    salary_offered = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Salary Offered"))
    benefits = models.TextField(verbose_name=_("Benefits"), blank=True)
    status = models.CharField(
        max_length=50,
        choices=JobOfferStatus.choices,
        default=JobOfferStatus.PENDING,
        verbose_name=_("Offer Status")
    )
    negotiation_notes = models.TextField(blank=True, null=True, verbose_name=_("Negotiation Notes"))
    final_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Final Salary")
    )
    created_at = models.DateTimeField(verbose_name=("Created At"),auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"),auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def __str__(self):
        return f"{self.title}"
        # return f"Offer {self.title} for {self.applicant.user.get_full_name()} - {self.job_opening.title} - {self.status}"
    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            ApplicantTracking.objects.create(
                applicant=self.applicant,
                job_opening=self.job_opening,
                stage="Offer",
                application_status=self.status,
                notes=f"Job offer status changed to {self.status}."
            )
#______________________JobOffer Model classes End_____________________#


#______________________Onboarding Model classes Start_____________________#
class OnboardingStatus(models.TextChoices):
    IN_PROGRESS = 'In Progress', _('In Progress')
    COMPLETED = 'Completed', _('Completed')
    PENDING = 'Pending', _('Pending')

class Onboarding(models.Model):
    job_offer = models.OneToOneField(
        JobOffer,
        on_delete=models.CASCADE,
        related_name='onboarding',
        verbose_name=_("Job Offer")
    )
    employee = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='onboardings',
        verbose_name=_("Employee"),
        limit_choices_to = filter_accepted_job_offers

    )
    job_opening = models.ForeignKey(
        JobOpening,
        on_delete=models.CASCADE,
        related_name='onboardings',
        verbose_name=_("Job Opening")
    )
    hiring_date = models.DateField(verbose_name=_("Hiring Date"))
    contract_signed = models.BooleanField(default=False, verbose_name=_("Contract Signed"))
    onboarding_completion = models.BooleanField(default=False, verbose_name=_("Onboarding Completion"))
    orientation_date = models.DateField(null=True, blank=True, verbose_name=_("Orientation Date"))
    assigned_mentor = models.ForeignKey(
        User,
        related_name='mentors',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Assigned Mentor"), 
        limit_choices_to = filter_mentors
    )
    training_schedule = models.TextField(blank=True, null=True, verbose_name=_("Training Schedule"))
    documents_submitted = models.BooleanField(default=False, verbose_name=_("Documents Submitted"))
    status = models.CharField(
        max_length=50,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.PENDING,
        verbose_name=_("Onboarding Status")
    )
    created_at = models.DateTimeField(verbose_name=("Created At"),auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"),auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def clean(self):
        super().clean()
        if self.employee != self.job_offer.applicant:
            raise ValidationError(_("Selected employee does not match the applicant in the Job Offer."))
        if self.job_opening != self.job_offer.job_opening:
            raise ValidationError(_("Selected job opening does not match the Job Opening in the Job Offer."))

    def __str__(self):
        return f"Onboarding for {self.employee.user.get_full_name()} - {self.job_opening.title}"
    def save(self, *args, **kwargs):
        # Automatically set the status field based on onboarding_completion
        if self.onboarding_completion:
            self.status = OnboardingStatus.COMPLETED
        else:
            self.status = OnboardingStatus.IN_PROGRESS

        # Save the current onboarding object
        super().save(*args, **kwargs)

        # Log this onboarding step in ApplicantTracking
        ApplicantTracking.objects.create(
            applicant=self.employee,
            job_opening=self.job_opening,
            stage="Onboarding",
            application_status = self.status,
            notes="Onboarding process updated."
        )
#______________________Onboarding Model classes End_____________________#

#______________________ApplicantTracking Model class Start_____________________#
class ApplicantTracking(models.Model):
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='trackings',
        verbose_name=_("Applicant")
    )
    job_opening = models.ForeignKey(
        JobOpening,
        on_delete=models.CASCADE,
        related_name='trackings',
        verbose_name=_("Job Opening")
    )
    stage = models.CharField(
        max_length=50,
        default='Application',
        verbose_name=_("Recruitment Stage")
    )
    application_status = models.CharField(
        max_length=50,
        default='Received',
        verbose_name=_("Status")
    )
    tracking_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Tracking Date"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    history = models.JSONField(default=list, blank=True, verbose_name=_("History"))
    created_at = models.DateTimeField(verbose_name=("Updated At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=("Updated At"), auto_now=True)
    is_deleted = models.BooleanField(verbose_name=_("Is Deleted"), default=False)

    def save(self, *args, **kwargs):
        if self.pk:
            previous = ApplicantTracking.objects.get(pk=self.pk)
            if previous.application_status != self.application_status:
                self.history.append({
                    'previous_status': previous.application_status,
                    'new_status': self.application_status,
                    'changed_at': timezone.now(),
                    'changed_by': kwargs.get('changed_by', None)
                })
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.applicant.user.get_full_name()} - {self.job_opening.title} - {self.application_status}"


#______________________ApplicantTracking Model class End_____________________#

#______________________CustomTicket Model classes Start_____________________#

class CustomTicket(Ticket):
    url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="URL of the Issue",
        help_text="The page where the issue was encountered."
    )

    class Meta:
        # Inherit metadata from Ticket without overriding unnecessarily
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"{self.ticket} - {self.title}"

# #______________________CustomTicket Model classes End_____________________#


class Issue(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issues')
    ticket = models.OneToOneField(Ticket, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachment = models.FileField(upload_to='issues/attachments/', null=True, blank=True)
    origin_url = models.URLField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

# class Issue(models.Model):
#     STATUS_CHOICES = (
#         ('pending', 'Pending'),
#         ('approved', 'Approved'),
#         ('refused', 'Refused'),
#     )

#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     attachment = models.FileField(upload_to='issues/', null=True, blank=True)
#     origin_url = models.URLField()
#     submitted_at = models.DateTimeField(auto_now_add=True)
#     ticket_id = models.IntegerField(null=True, blank=True)  # Link to Support ticket
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
#     supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_issues')
#     refusal_reason = models.TextField(null=True, blank=True)

#     def __str__(self):
#         return self.title

#     def get_support_ticket_status(self):
#         """Fetch the status of the linked Support ticket."""
#         if not self.ticket_id:
#             return "Not Submitted"
#         try:
#             response = requests.get(f'http://127.0.0.1:8001/api/tickets/{self.ticket_id}/', timeout=5)
#             if response.status_code == 200:
#                 ticket_data = response.json()
#                 return ticket_data.get('status', 'Unknown')
#             return "Error Fetching Status"
#         except requests.RequestException:
#             return "Error Fetching Status"

class Feedback(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        verbose_name=_("Related Ticket"),
        help_text=_("The ticket this feedback pertains to.")
    )
    message = models.TextField(
        _("Feedback Message"),
        help_text=_("Comment or resolution provided to the user.")
    )
    ticket_status = models.IntegerField(
        _("Ticket Status at Feedback"),
        choices=Ticket.STATUS_CHOICES,
        help_text=_("The status of the ticket when feedback was provided.")
    )
    received_at = models.DateTimeField(
        _("Received At"),
        auto_now_add=True,
        help_text=_("Date and time the feedback was created.")
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Sent By"),
        help_text=_("The staff member who provided the feedback.")
    )

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedback Entries")
        ordering = ['-received_at']

    def __str__(self):
        return f"Feedback for {self.ticket.ticket_for_url} on {self.received_at}"

    # def save(self, *args, **kwargs):
    #     if not self.pk and not self.sent_by.groups.filter(name='Supervisors').exists():
    #         raise ValidationError(_("Only supervisors can create or edit feedback."))
    #     super().save(*args, **kwargs)

# class Feedback(models.Model):
#     issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
#     message = models.TextField()
#     received_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Feedback for {self.issue.title}"