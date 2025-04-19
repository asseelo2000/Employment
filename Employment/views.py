from urllib.parse import urlparse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from datetime import date
from django.contrib import messages
from Employment.models import Applicant, JobApplication, JobOpening, JobOpening, JobOffer, JobOpeningStatus
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import os
from django.core.exceptions import ValidationError
from .models import Issue, Feedback
from helpdesk.views.public import CreateTicketView
from helpdesk.models import Ticket
from .forms import CustomPublicTicketForm
import requests
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
import logging
from helpdesk.views import staff as helpdesk_staff
from helpdesk.models import FollowUp
from .decorators import supervisor_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5M

logger = logging.getLogger(__name__)

@supervisor_required
def ticket_list(request):
    return helpdesk_staff.ticket_list(request)

@supervisor_required
def view_ticket(request, ticket_id):
    return helpdesk_staff.view_ticket(request, ticket_id)

@api_view(['POST'])
@csrf_exempt
def receive_feedback(request):
    logger.debug(f"Received request: {request.POST}")
    
    # Validate token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Token ') or auth_header.split(' ')[1] != settings.EMPLOYMENT2_API_KEY:
        logger.error(f"Invalid token: {auth_header}")
        return Response({'error': 'Invalid or missing token'}, status=401)

    ticket_id = request.POST.get('ticket_id')
    message = request.POST.get('message')
    ticket_status = request.POST.get('ticket_status')
    user_id = request.POST.get('user_id', 'Support')  # Default to 'Support' if not provided
    logger.debug(f"Extracted - ticket_id: {ticket_id}, message: {message}, ticket_status: {ticket_status}, user_id: {user_id}")

    if not ticket_id or not message:
        logger.error(f"Missing data - ticket_id: {ticket_id}, message: {message}")
        return Response({'error': 'Missing ticket_id or message'}, status=400)

    try:
        # Find the ticket using origin_ticket_id (from Support) or id
        try:
            ticket = Ticket.objects.get(external_ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            ticket = Ticket.objects.get(id=ticket_id)
        logger.debug(f"Found ticket: {ticket.id}, external_ticket_id: {ticket.external_ticket_id}")

        # Get or create a user for Support feedback (e.g., a system user)
        try:
            support_user = User.objects.get(username='support_system')
        except User.DoesNotExist:
            support_user = User.objects.create_user(
                username='support_system',
                email='support@system.com',
                password='defaultpassword'  # Set a secure password or use a secret
            )
            logger.debug("Created support_system user")

        # Create a FollowUp as a comment
        followup = FollowUp.objects.create(
            ticket=ticket,
            user=support_user,  # Assign to a system user
            title=f"رد من الدعم الفني على التذكرة  (Ticket #{ticket_id})",
            comment=message,
            public=True,  # Make it visible to the submitter
            date=timezone.now(),
        )

        for field in Ticket._meta.get_fields():
                field_name = field.name
                field_value = getattr(ticket, field_name, None)
                print(f"{field_name}: {field_value}")


        # Optionally update ticket status if provided
        if ticket_status and ticket_status.isdigit():
            new_status = int(ticket_status)
            if new_status in [choice[0] for choice in Ticket.STATUS_CHOICES]:
                ticket.status = new_status
                ticket.save()
                logger.debug(f"Updated ticket status to: {ticket.get_status_display()}")

        # Send email to submitter (optional)
        if ticket.submitter_email:
            try:
                send_mail(
                    'New Feedback from Support',
                    f'New feedback has been added to your ticket "{ticket.title}".\n'
                    f'The feedback is: "{message}".\n'
                    f'Status: {ticket.get_status_display()}\n'
                    f'View your ticket at: {ticket.ticket_url}\n',
                    settings.DEFAULT_FROM_EMAIL,
                    [ticket.submitter_email],
                    fail_silently=False,
                )
                logger.debug(f"Email sent to: {ticket.submitter_email}")
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                # Don’t fail the request due to email error

        return Response({'status': 'Feedback received as follow-up'}, status=200)

    except Ticket.DoesNotExist:
        logger.error(f"Ticket not found for external_ticket_id or id: {ticket_id}")
        return Response({'error': 'Ticket not found for this ticket ID.'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response({'error': f'Error processing feedback: {str(e)}'}, status=500)
    
# @api_view(['POST'])
# def receive_feedback(request):
#     # Validate token
#     auth_header = request.headers.get('Authorization', '')
#     if not auth_header.startswith('Token ') or auth_header.split(' ')[1] != settings.EMPLOYMENT2_API_KEY:
#         return Response({'error': 'Invalid or missing token'}, status=401)

#     ticket_id = request.data.get('ticket_id')
#     message = request.data.get('message')
#     try:
#         issue = Issue.objects.get(ticket_id=ticket_id)
#         feedback = Feedback.objects.create(issue=issue, message=message)
#         send_mail(
#             'Feedback Received From Helpdesk',
#             f'You have received feedback on your issue with title: {issue.title}.\n'
#             f'The issue you were working on is "{issue.description}".\n'
#             f'The feedback is "{feedback.message}". You can recheck the issue on the link "{issue.origin_url}".\n'
#             f'Please check your feedback page for more details.',
#             settings.DEFAULT_FROM_EMAIL,
#             [issue.user.email],
#             fail_silently=False,
#         )
#         return Response({'status': 'Feedback received'}, status=200)
#     except Issue.DoesNotExist:
#         return Response({'error': 'Issue not found for this ticket ID.'}, status=404)

@login_required
@require_POST
def send_internal_feedback(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check if the user has permission to send feedback (e.g., staff or supervisor)
    if not request.user.is_staff:  # Adjust permission logic as needed
        return JsonResponse({'error': 'Permission denied'}, status=403)

    feedback_message = request.POST.get('feedback_message', '').strip()
    if not feedback_message:
        return JsonResponse({'error': 'Feedback message cannot be empty'}, status=400)

    # Create the Feedback instance
    feedback = Feedback.objects.create(
        ticket=ticket,
        message=feedback_message,
        ticket_status=ticket.status,  # Current ticket status
        sent_by=request.user
    )

    # Optionally send an email to the ticket submitter
    if ticket.submitter_email:
        subject = f"Feedback on Your Ticket [{ticket.ticket_for_url}]"
        message = (
            f"Dear {ticket.submitter_email},\n\n"
            f"We have an update on your ticket '{ticket.title}':\n\n"
            f"Status: {ticket.get_status_display()}\n"
            f"Feedback: {feedback_message}\n\n"
            f"View your ticket: {ticket.ticket_url}\n\n"
            f"Regards,\nThe Employment2 Support Team"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [ticket.submitter_email],
            fail_silently=True,
        )

    return JsonResponse({'message': 'Feedback sent successfully'}, status=200)    

@login_required
@require_POST
def send_external_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check if the user is a supervisor (adjust permission logic as needed)
    if not request.user.groups.filter(name='Supervisors').exists() and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    ticket_data = request.POST.get('ticket_data', '')
    if not ticket_data:
        return JsonResponse({'error': 'No ticket data provided'}, status=400)

    try:
        # Parse the JSON data from the form
        ticket_info = json.loads(ticket_data)
        
        # Get the original origin_url
        original_url = ticket_info.get('origin_url', ticket.submitted_from_url or '')

        # Transform the origin_url into the reference format
        reference_url = transform_url_to_reference(original_url)

        # Handle attachments if present
        files = {}
        if ticket.followup_set.filter(followupattachment__isnull=False).exists():
            attachment = ticket.followup_set.filter(followupattachment__isnull=False).first().followupattachment_set.first()
            files['attachment'] = (attachment.filename, attachment.file.file, attachment.mime_type)

        # Prepare payload for the external support system
        payload = {
            'company_id': 'employment2',  # Hardcoded for Employment2
            'title': ticket_info.get('title', ticket.title),
            'description': ticket_info.get('description', ticket.description),
            'user_email': ticket_info.get('user_email', ticket.submitter_email),
            'user_id': str(request.user.id),  # Supervisor’s ID as string
            'user_first_name': request.user.first_name,
            'user_last_name': request.user.last_name,
            'attachment':   ticket_info.get('attachment') or '',
            'user_phone': request.user.phone_number if hasattr(request.user, 'phone_number') else '',
            'origin_url': reference_url,  # Use the transformed reference instead of the original URL
            'submitted_at': ticket_info.get('submitted_at', ticket.created.isoformat()),
            'origin_ticket_id': str(ticket.id),  # Employment2 ticket ID
            'ticket_type': ticket.ticket_type,

        }
        print(payload)

        # Add Authorization header (example: Bearer token)
        headers = {
            'Authorization': f'Token {settings.SUPPORT_API_KEY}',  # Replace with your token or key
        }

        # Send request to external support API
        response = requests.post(
            'http://127.0.0.1:8001/api/submit-ticket/',
            data=payload,
            files=files if files else None,
            headers=headers,
        )

        if response.status_code == 201:
            external_ticket_id = response.json().get('ticket_id')
            # Optionally store the external ticket ID in the Ticket model
            ticket.external_ticket_id = external_ticket_id  # Requires field in Ticket model
            ticket.save()
            return JsonResponse({'message': 'Ticket sent successfully', 'ticket_id': external_ticket_id}, status=200)
        else:
            return JsonResponse({'error': f'Failed to send ticket: {response.text}'}, status=response.status_code)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid ticket data format'}, status=400)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Error sending to Support: {str(e)}'}, status=500)
    
def transform_url_to_reference(url):
    if not url:
        return ""

    # Parse the URL
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')

    # Split the path into components
    parts = path.split('/')

    # Default values
    reference_parts = []

    # URL structure: /admin/app/model/id/action/
    if len(parts) >= 2 and parts[0] == 'admin':
        if len(parts) >= 2:
            reference_parts.append(f"app-{parts[1].capitalize()}")
        if len(parts) >= 3:
            reference_parts.append(f"model-{parts[2]}")
        if len(parts) >= 4:
            reference_parts.append(f"object-{parts[3]}")
        if len(parts) >= 5:
            reference_parts.append(f"{parts[4]}-form")

    # Construct the reference
    reference = " ".join(f"#{part}" for part in reference_parts)
    return reference

# @login_required
# def submit_issue(request):
#     if request.method == 'POST':
#         supervisor = User.objects.filter(groups__name='Supervisors').first()
#         if not supervisor:
#             messages.error(request, 'No supervisor available to review your issue.')
#             return redirect(request.META.get('HTTP_REFERER', '/admin/'))

#         ticket = Ticket(
#             title=request.POST['title'],
#             description=request.POST['description'],
#             submitter_email=request.user.email,
#             submitted_from_url=request.POST['origin_url'],
#             status='1',  # Initial status
#         )
#         if 'attachment' in request.FILES:
#             ticket.attachment = request.FILES['attachment']
#         ticket.save()

#         # Notify supervisor via email (optional)
#         supervisors = User.objects.filter(groups__name='Supervisors')
#         if not supervisors:
#             messages.error(request, 'No supervisors available to review your ticket.')
#             return redirect(request.META.get('HTTP_REFERER', '/admin/'))
#         send_mail(
#             'New Internal Ticket Submitted',
#             f'A new ticket "{ticket.title}" has been submitted by {request.user.username} for review.',
#             settings.DEFAULT_FROM_EMAIL,
#             [supervisor.email for supervisor in supervisors],
#             fail_silently=True,
#         )

#         messages.success(request, 'Your ticket has been submitted for supervisor review.')
#         return redirect(request.META.get('HTTP_REFERER', '/admin/'))  # Redirect to the referring page
#     return redirect(request.META.get('HTTP_REFERER', '/admin/'))

# @login_required
# def submit_issue(request):
#     if request.method == 'POST':
#         supervisor = User.objects.filter(groups__name='Supervisors').first()
#         if not supervisor:
#             messages.error(request, 'No supervisor available to review your issue.')
#             return redirect(request.META.get('HTTP_REFERER', '/admin/'))

#         issue = Issue(
#             user=request.user,
#             title=request.POST['title'],
#             description=request.POST['description'],
#             attachment=request.FILES.get('attachment'),
#             origin_url=request.POST['origin_url'],
#             supervisor=supervisor,
#             status='pending',
#         )
#         issue.save()

#         # Notify supervisor via email (optional)
#         send_mail(
#             'New Issue Submitted',
#             f'A new issue "{issue.title}" has been submitted for your review by {request.user.username}.',
#             settings.DEFAULT_FROM_EMAIL,
#             [supervisor.email],
#             fail_silently=True,
#         )

#         messages.success(request, 'Your issue has been submitted to the supervisor for review.')
#         return redirect(request.META.get('HTTP_REFERER', '/admin/'))  # Redirect to the referring page
#     return redirect(request.META.get('HTTP_REFERER', '/admin/'))

# @api_view(['POST'])
# def receive_feedback(request):
#     ticket_id = request.data['ticket_id']
#     message = request.data['message']
#     try:
#         issue = Issue.objects.get(ticket_id=ticket_id)
#         feedback = Feedback.objects.create(issue=issue, message=message)
#         send_mail(
#             'Feedback Received From Helpdesk',
#             f'You have received feedback on your issue with title: {issue.title}.\n'
#             f'The issue you were working on is "{issue.description}".\n'
#             f'The feedback is "{feedback.message}". You can recheck the issue on the link "{issue.origin_url}".\n'
#             f'Please check your feedback page for more details.',
#             settings.DEFAULT_FROM_EMAIL,
#             [issue.user.email],
#             fail_silently=False,
#         )
#         return Response({'status': 'Feedback received'}, status=200)
#     except Issue.DoesNotExist:
#         return Response({'error': 'Issue not found for this ticket ID.'}, status=404)

@login_required
def view_feedback(request):
    feedbacks = Feedback.objects.filter(issue__user=request.user)
    return render(request, 'feedback.html', {'feedbacks': feedbacks})



# @login_required
# def submit_issue(request):
#     if request.method == 'POST':
#         # Redirect to admin add form with prefilled user
#         return redirect(f'/admin/Employment/issue/add/?user={request.user.id}&origin_url={request.POST.get("origin_url", "")}')
#     return redirect('admin:Employment_issue_changelist')  # Fallback to issue list

# @login_required
# def submit_issue(request):
#     if request.method == 'POST':
#         issue = Issue.objects.create(
#             user=request.user,
#             title=request.POST['title'],
#             description=request.POST['description'],
#             attachment=request.FILES.get('attachment'),
#             origin_url=request.POST['origin_url'],  # Use the form field instead
#         )
#         # Send to Support API
#         payload = {
#             'title': issue.title,
#             'description': issue.description,
#             'user_email': request.user.email,
#             'user_id': request.user.id,
#             'origin_url': issue.origin_url,
#             'submitted_at': issue.submitted_at.isoformat(),
#         }
#         files = {'attachment': issue.attachment.file} if issue.attachment else {}
#         response = requests.post(
#             'http://127.0.0.1:8001/api/submit-ticket/',
#             data=payload,
#             files=files,
#         )
#         if response.status_code == 201:
#             issue.ticket_id = response.json()['ticket_id']
#             issue.save()
#             messages.success(request, 'Issue submitted successfully. We will get the feedback to you soon.')
#         else:
#             # Add error message if API call fails
#             messages.error(request, 'Failed to submit your issue. Please try again.')
#         # Redirect back to the admin index or referring page
#         return redirect(request.META.get('HTTP_REFERER', 'admin:index'))
    
#     return redirect('admin:index')

class CustomPublicTicketView(CreateTicketView):
    form_class = CustomPublicTicketForm
    template_name = 'helpdesk/public_create_ticket.html'

# Create your views here.
def index(request):
    return render(request, "portal/index.html")


def signup(request):
    if request.method == "POST":
        username = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        phone = request.POST["phone"]

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("/signup")

        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=confirm_password,
        )
        applicants = Applicant.objects.create(user=user, phone=phone, first_name=first_name,last_name=last_name)
        user.save()
        applicants.save()
        return render(request, "users/sign_in.html")
    return render(request, "users/signup.html")


def sign_in(request):
    if request.method == "POST":
        username = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)

        if user is not None:
            user1 = Applicant.objects.get(user=user)
            login(request, user)
            messages.success(request, "loged in successfully")
            return redirect("employment:all_jobs")
        else:
            messages.error(request, "Invalid Credentials")
            return redirect("employment:sign_in")
    return render(request, "users/sign_in.html")


def all_jobs(request):
    # Filter JobOpening objects to include only those with OPEN status
    jobs = JobOpening.objects.filter(status=JobOpeningStatus.OPEN)  
    print(jobs)
    return render(request, "portal/all_jobs.html", {"jobs": jobs})


def job_detail(request, myid):
    job = JobOpening.objects.get(id=myid)
    return render(request, "portal/job_detail.html", {"job": job})

def validate_resume(resume):
    ext = os.path.splitext(resume.name)[1].lower()
    if ext.replace('.', '') not in ALLOWED_EXTENSIONS:
        raise ValidationError('Unsupported file extension. Allowed extensions are: pdf, doc, docx.')
    if resume.size > MAX_FILE_SIZE:
        raise ValidationError('File size exceeds the allowed limit of 5MB.')
    
@login_required
def job_apply(request, myid):
    job = get_object_or_404(JobOpening, id=myid)
    current_date = timezone.now().date()

    # # Check if the job is open for applications
    # if job.closing_date < current_date:
    #     messages.error(request, "This job posting has closed.")
    #     return redirect('employment:job_detail', myid=myid)
    # elif job.posted_date > current_date:
    #     messages.error(request, "This job posting is not yet open.")
    #     return redirect('employment:job_detail', myid=myid)

    # Fetch the applicant profile
    try:
        applicant = Applicant.objects.get(user=request.user)
    except Applicant.DoesNotExist:
        messages.error(request, "Applicant profile not found. Please complete your profile before applying.")
        return redirect('employment:sign_in')

    if request.method == "POST":
        resume = request.FILES.get('resume')
        cover_letter = request.POST.get('cover_letter', '')

        if not resume:
            messages.error(request, "Please upload your resume.")
            return redirect('employment:job_detail', myid=myid)
        
        # Validate resume FILE type and FILE size
        try:
            validate_resume(resume)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect('employment:job_detail', myid=myid)
        
        # Check if the applicant has already applied to this job
        if JobApplication.objects.filter(job_opening=job, applicant=applicant).exists():
            messages.warning(request, "You have already applied to this job.")
            return redirect('employment:job_detail', myid=myid)

        # Create the job application
        JobApplication.objects.create(
            job_opening=job,
            branch=job.branch,
            applicant=applicant,
            resume=resume,
            cover_letter=cover_letter
        )

        messages.success(request, "Your application has been submitted successfully.")
        return redirect('employment:job_detail', myid=myid)

    # If the request method is not POST, redirect to job detail page
    return redirect('employment:job_detail', myid=myid)



