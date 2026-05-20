from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(role):
    """Decorator that restricts view access to users with a specific role."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')
            if request.user.role != role:
                messages.error(request, f"This page is only accessible to {role}s.")
                return redirect('trips:index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
