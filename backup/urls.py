from django.urls import path
from .views import BackupCreateView, BackupIndexView, BackupRestoreView

app_name = "backup"

urlpatterns = [
    path("", BackupIndexView.as_view(), name="index"),
    path("create/", BackupCreateView.as_view(), name="create"),
    path("restore/", BackupRestoreView.as_view(), name="restore"),
]
