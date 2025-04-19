from helpdesk.models import Queue
from django.conf import settings

def default_queue(request):
    default_queue = Queue.objects.filter(is_default=True).first()
    if not default_queue:
        # Create a default queue if none exists
        default_queue = Queue.objects.create(
            title=settings.HELPDESK_DEFAULT_QUEUE,
            is_default=True,
            allow_public_submission=True
        )
    return {'default_queue_id': default_queue.id if default_queue else None}