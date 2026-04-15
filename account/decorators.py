from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def teacher_required(view_func):
    """Decorator that restricts access to teachers only.
    Students who try to access will be redirected to their dashboard with an error message.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Check if user has a profile and is a teacher
        profile = getattr(request.user, 'profile', None)
        if profile is None or not profile.is_teacher:
            messages.error(request, '⛔ Access Denied — This area is for teachers only.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)
    return _wrapped_view
