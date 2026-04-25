from django.db.utils import OperationalError, ProgrammingError

from .models import PondokProfile


def pondok_profile(request):
    try:
        profile = PondokProfile.get_solo()
        show_welcome_toast = bool(request.session.pop("show_welcome_toast", False))
    except (OperationalError, ProgrammingError):
        profile = PondokProfile()
        show_welcome_toast = False
    return {
        "pondok_profile": profile,
        "pondok_profile_complete": profile.is_complete(),
        "show_welcome_toast": show_welcome_toast,
    }
