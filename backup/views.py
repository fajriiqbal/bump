from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.management import call_command
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import BackupRestoreForm


class FinanceAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, "role", "") == "admin"


class BackupIndexView(FinanceAdminRequiredMixin, TemplateView):
    template_name = "backup/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backup_dir = Path(settings.BASE_DIR) / "media" / "backups"
        context["latest_backup"] = backup_dir / "backup.json"
        context["backup_exists"] = context["latest_backup"].exists()
        context["restore_form"] = kwargs.get("restore_form") or BackupRestoreForm()
        return context


class BackupCreateView(FinanceAdminRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        call_command("create_backup")
        messages.success(request, "Backup berhasil dibuat.")
        return redirect("backup:index")


class BackupRestoreView(FinanceAdminRequiredMixin, FormView):
    template_name = "backup/index.html"
    form_class = BackupRestoreForm
    success_url = "/backup/"

    def form_valid(self, form):
        uploaded = form.cleaned_data["backup_file"]
        backup_dir = Path(settings.BASE_DIR) / "media" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / uploaded.name
        with target.open("wb") as destination:
            for chunk in uploaded.chunks():
                destination.write(chunk)
        call_command("loaddata", target)
        messages.success(self.request, f"Restore berhasil dijalankan dari {target.name}.")
        return redirect("backup:index")

    def form_invalid(self, form):
        backup_dir = Path(settings.BASE_DIR) / "media" / "backups"
        return self.render_to_response(
            self.get_context_data(
                restore_form=form,
                latest_backup=backup_dir / "backup.json",
                backup_exists=(backup_dir / "backup.json").exists(),
            )
        )
