from django.db.models import Q

# PreEmploymentTest model
def filter_evaluators():
    return Q(groups__name="evaluators")

# JobOffer model
def filter_final_evaluations():
    return Q(evaluations__is_final=True)

# JobOffer model
def filter_accepted_job_offers():
    from ..models import JobOfferStatus
    return Q(job_offers_applicants__status=JobOfferStatus.ACCEPTED)

# JobOpening model
def filter_active_job_openings():
    from ..models import JobOpeningStatus
    return Q(status=JobOpeningStatus.OPEN, is_active=True)

# Interview model
def filter_interview_applicants():
    from ..models import TestResult
    return Q(pre_employment_tests__result=TestResult.PASS)

# Interview model
def filter_interviewers():
    return Q(groups__name="interviewers")

# Branch model
def filter_alrasheed_admins():
    return Q(groups__name="alrasheed_admins")

# RecruitmentCampaign model
def filter_organizers():
    return Q(groups__name="organizers")

# ApplicantEvaluation model
def filter_final_interview_stage():
    from ..models import InterviewStage
    return Q(interviews_applicant__interview_stage=InterviewStage.FINAL)  # Adjust for `InterviewStage.FINAL`

# Onboarding model
def filter_mentors():
    return Q(groups__name="mentors")
