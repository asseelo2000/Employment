from django.db.models.signals import post_save
from django.dispatch import receiver

from Employment.models import ApplicantTracking, JobApplication

@receiver(post_save, sender=JobApplication)
def update_applicant_tracking(sender, instance, created, **kwargs):
    if created:
        ApplicantTracking.objects.create(
            applicant=instance.applicant,
            job_opening=instance.job_opening,
            application_status=instance.status,
            notes="Application received."
        )
    else:
        tracking = ApplicantTracking.objects.filter(
            applicant=instance.applicant,
            job_opening=instance.job_opening
        ).order_by('-tracking_date').first()
        if tracking:
            tracking.application_status = instance.status
            tracking.notes = "Status updated to " + instance.get_status_display()
            tracking.save()
        else:
            ApplicantTracking.objects.create(
                applicant=instance.applicant,
                job_opening=instance.job_opening,
                application_status=instance.status,
                notes="Application status updated."
            )
