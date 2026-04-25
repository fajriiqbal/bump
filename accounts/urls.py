from django.urls import path
from .views import CustomLoginView, PondokProfileSetupView, custom_logout_view

app_name = "accounts"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", custom_logout_view, name="logout"),
    path("profile/", PondokProfileSetupView.as_view(), name="profile_setup"),
]
