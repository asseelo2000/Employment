from django.http import HttpResponseForbidden
from functools import wraps

def supervisor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Supervisors').exists() or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You must be a supervisor to access this page.")
    return _wrapped_view