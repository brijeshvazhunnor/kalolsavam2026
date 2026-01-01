from django.shortcuts import redirect
from django.contrib import messages

from django.shortcuts import redirect
from django.contrib import messages
from .models import SiteSetting


def registration_open_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        setting = SiteSetting.objects.first()

        if not setting or not setting.allow_student_registration:
            messages.error(
                request,
                "Student registration is currently disabled by the administrator."
            )
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
