from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(role):
    """Logged-out users go to the login page; users with another role get a 403."""

    def decorator(view):
        @wraps(view)
        def _wrapped(request, *args, **kwargs):
            if request.user.role != role:
                raise PermissionDenied("You do not have access to this page.")
            return view(request, *args, **kwargs)

        return login_required(_wrapped)

    return decorator


resident_required = role_required(User.Role.RESIDENT)
staff_required = role_required(User.Role.STAFF)
