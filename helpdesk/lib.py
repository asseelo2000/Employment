"""
django-helpdesk - A Django powered ticket tracker for small enterprise.

(c) Copyright 2008 Jutda. All Rights Reserved. See LICENSE for details.

lib.py - Common functions (eg multipart e-mail)
"""


from datetime import date, datetime, time
from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.encoding import smart_str
from helpdesk.settings import CUSTOMFIELD_DATE_FORMAT, CUSTOMFIELD_DATETIME_FORMAT, CUSTOMFIELD_TIME_FORMAT
import logging
import mimetypes


logger = logging.getLogger('helpdesk')


def ticket_template_context(ticket):
    context = {}

    for field in ('title', 'created', 'modified', 'submitter_email','submitted_from_url',
                  'status', 'get_status_display', 'on_hold', 'description',
                  'resolution', 'priority', 'get_priority_display',
                  'last_escalation', 'ticket', 'ticket_for_url', 'merged_to',
                  'get_status', 'ticket_url', 'staff_url', '_get_assigned_to'
                  ):
        attr = getattr(ticket, field, None)
        if callable(attr):
            context[field] = '%s' % attr()
        else:
            context[field] = attr
    context['assigned_to'] = context['_get_assigned_to']

    return context


def queue_template_context(queue):
    context = {}

    for field in ('title', 'slug', 'email_address', 'from_address', 'locale'):
        attr = getattr(queue, field, None)
        if callable(attr):
            context[field] = attr()
        else:
            context[field] = attr

    return context


def safe_template_context(ticket):
    """
    Return a dictionary that can be used as a template context to render
    comments and other details with ticket or queue parameters. Note that
    we don't just provide the Ticket & Queue objects to the template as
    they could reveal confidential information. Just imagine these two options:
        * {{ ticket.queue.email_box_password }}
        * {{ ticket.assigned_to.password }}

    Ouch!

    The downside to this is that if we make changes to the model, we will also
    have to update this code. Perhaps we can find a better way in the future.
    """

    context = {
        'queue': queue_template_context(ticket.queue),
        'ticket': ticket_template_context(ticket),
    }
    context['ticket']['queue'] = context['queue']
    context['ticket']['company'] = ticket.company.name if ticket.company else "Unknown"
    context['ticket']['company_id'] = ticket.company.company_id if ticket.company else None
    
    return context


def text_is_spam(text, request):
    # Based on a blog post by 'sciyoshi':
    # http://sciyoshi.com/blog/2008/aug/27/using-akismet-djangos-new-comments-framework/
    # This will return 'True' is the given text is deemed to be spam, or
    # False if it is not spam. If it cannot be checked for some reason, we
    # assume it isn't spam.
    try:
        from akismet import Akismet
    except ImportError:
        return False
    from django.contrib.sites.models import Site
    from django.core.exceptions import ImproperlyConfigured
    try:
        site = Site.objects.get_current()
    except ImproperlyConfigured:
        site = Site(domain='configure-django-sites.com')

    # see https://akismet.readthedocs.io/en/latest/overview.html#using-akismet

    apikey = None

    if hasattr(settings, 'TYPEPAD_ANTISPAM_API_KEY'):
        apikey = settings.TYPEPAD_ANTISPAM_API_KEY
    elif hasattr(settings, 'PYTHON_AKISMET_API_KEY'):
        # new env var expected by python-akismet package
        apikey = settings.PYTHON_AKISMET_API_KEY
    elif hasattr(settings, 'AKISMET_API_KEY'):
        # deprecated, but kept for backward compatibility
        apikey = settings.AKISMET_API_KEY
    else:
        return False

    ak = Akismet(
        blog_url='http://%s/' % site.domain,
        key=apikey,
    )

    if hasattr(settings, 'TYPEPAD_ANTISPAM_API_KEY'):
        ak.baseurl = 'api.antispam.typepad.com/1.1/'

    if ak.verify_key():
        ak_data = {
            'user_ip': request.META.get('REMOTE_ADDR', '127.0.0.1'),
            'user_agent': request.headers.get('User-Agent', ''),
            'referrer': request.headers.get('Referer', ''),
            'comment_type': 'comment',
            'comment_author': '',
        }

        return ak.comment_check(smart_str(text), data=ak_data)

    return False


def process_attachments(followup, attached_files):
    max_email_attachment_size = getattr(
        settings, 'HELPDESK_MAX_EMAIL_ATTACHMENT_SIZE', 512000)
    attachments = []
    errors = set()

    for attached in attached_files:

        if attached.size:
            from helpdesk.models import FollowUpAttachment

            filename = smart_str(attached.name)
            att = FollowUpAttachment(
                followup=followup,
                file=attached,
                filename=filename,
                mime_type=attached.content_type or
                mimetypes.guess_type(filename, strict=False)[0] or
                'application/octet-stream',
                size=attached.size,
            )
            try:
                att.full_clean()
            except ValidationError as e:
                errors.add(e)
            else:
                att.save()

                if attached.size < max_email_attachment_size:
                    # Only files smaller than 512kb (or as defined in
                    # settings.HELPDESK_MAX_EMAIL_ATTACHMENT_SIZE) are sent via
                    # email.
                    attachments.append([filename, att.file])

    if errors:
        raise ValidationError(list(errors))

    return attachments


def format_time_spent(time_spent):
    """Format time_spent attribute to "[H]HHh:MMm" text string to be allign in
    all graphical outputs
    """
    if time_spent:
        time_spent = "{0:02d}h:{1:02d}m".format(
            int(time_spent.total_seconds()) // 3600,
            int(time_spent.total_seconds()) % 3600 // 60
        )
    else:
        time_spent = ""
    return time_spent


def convert_value(value):
    """ Convert date/time data type to known fixed format string """
    if type(value) is datetime:
        return value.strftime(CUSTOMFIELD_DATETIME_FORMAT)
    elif type(value) is date:
        return value.strftime(CUSTOMFIELD_DATE_FORMAT)
    elif type(value) is time:
        return value.strftime(CUSTOMFIELD_TIME_FORMAT)
    else:
        return value


def daily_time_spent_calculation(earliest, latest, open_hours):
    """Returns the number of seconds for a single day time interval according to open hours."""

    time_spent_seconds = 0

    # avoid rendering day in different locale
    weekday = ('monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday')[earliest.weekday()]
    
    # enforce correct settings
    MIDNIGHT = 23.9999
    start, end = open_hours.get(weekday, (0, MIDNIGHT))
    if not 0 <= start <= end <= MIDNIGHT:
        raise ImproperlyConfigured("HELPDESK_FOLLOWUP_TIME_SPENT_OPENING_HOURS"
                        f" setting for {weekday} out of (0, 23.9999) boundary")
    
    # transform decimals to minutes and seconds
    start_hour, start_minute, start_second = int(start), int(start % 1 * 60), int(start * 60 % 1 * 60)
    end_hour, end_minute, end_second = int(end), int(end % 1 * 60), int(end * 60 % 1 * 60)

    # translate time for delta calculation
    earliest_f = earliest.hour + earliest.minute / 60 + earliest.second / 3600
    latest_f = latest.hour + latest.minute / 60 + latest.second / (60 * 60) + latest.microsecond / (60 * 60 * 999999)

    # if latest time is midnight and close hour is midnight, add a second to the time spent
    if latest_f >= MIDNIGHT and end == MIDNIGHT:
        time_spent_seconds += 1
    
    if earliest_f < start:
        earliest = earliest.replace(hour=start_hour, minute=start_minute, second=start_second)
    elif earliest_f >= end:
        earliest = earliest.replace(hour=end_hour, minute=end_minute, second=end_second)
    
    if latest_f < start:
        latest = latest.replace(hour=start_hour, minute=start_minute, second=start_second)
    elif latest_f >= end:
        latest = latest.replace(hour=end_hour, minute=end_minute, second=end_second)
    
    day_delta = latest - earliest
    time_spent_seconds += day_delta.seconds
    
    return time_spent_seconds