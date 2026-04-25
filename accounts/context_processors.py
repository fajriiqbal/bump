from .models import PondokProfile


def pondok_profile(request):
    profile = PondokProfile.get_solo()
    show_welcome_toast = bool(request.session.pop("show_welcome_toast", False))
    return {
        "pondok_profile": profile,
        "pondok_profile_complete": profile.is_complete(),
        "show_welcome_toast": show_welcome_toast,
    }
