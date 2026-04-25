from functools import wraps
from django.contrib.auth.decorators import user_passes_test


def role_required(*roles):
    def check(user):
        return user.is_authenticated and (user.is_superuser or getattr(user, "role", None) in roles)

    return user_passes_test(check)


def admin_required(view_func):
    @wraps(view_func)
    @role_required("admin")
    def _wrapped(*args, **kwargs):
        return view_func(*args, **kwargs)

    return _wrapped
