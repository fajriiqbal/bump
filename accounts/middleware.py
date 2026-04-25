from django.shortcuts import redirect
from django.urls import reverse

from .models import PondokProfile


class PondokProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, "role", "") == "admin"):
            profile = PondokProfile.get_solo()
            if not profile.is_complete():
                allowed_paths = (
                    reverse("accounts:logout"),
                    reverse("accounts:profile_setup"),
                    "/admin/",
                    "/static/",
                    "/media/",
                )
                if not request.path.startswith(allowed_paths):
                    return redirect(reverse("accounts:profile_setup"))
        return self.get_response(request)
