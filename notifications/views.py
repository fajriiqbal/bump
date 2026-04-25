from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from finance.models import Bill
from django.urls import reverse
from .forms import MessageTemplateForm, WhatsAppGatewayForm
from .models import MessageLog, MessageTemplate, WhatsAppGatewayConfig
from .services import build_bill_reminder_message, build_student_reminder_message, build_whatsapp_url, send_whatsapp


class NotificationAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, "role", "") == "admin"


class NotificationIndexView(NotificationAdminRequiredMixin, TemplateView):
    template_name = "notifications/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gateway = WhatsAppGatewayConfig.objects.filter(active=True).first()
        templates = MessageTemplate.objects.filter(active=True).order_by("title")
        logs = MessageLog.objects.order_by("-created_at")[:10]
        pending_bills = (
            Bill.objects.exclude(status=Bill.Status.LUNAS)
            .select_related("santri", "jenis_pembayaran")
            .order_by("santri__nama_lengkap", "periode_tahun", "periode_bulan")
        )

        student_rows = []
        current_student_id = None
        current_group = None
        for bill in pending_bills:
            if bill.santri_id != current_student_id:
                if current_group:
                    student_rows.append(current_group)
                current_student_id = bill.santri_id
                current_group = {
                    "student": bill.santri,
                    "bills": [],
                }
            current_group["bills"].append(bill)

        if current_group:
            student_rows.append(current_group)

        for row in student_rows:
            bills = row["bills"]
            row["bill_count"] = len(bills)
            row["total_tagihan"] = sum((bill.total_tagihan for bill in bills), 0)
            row["total_dibayar"] = sum((bill.total_dibayar for bill in bills), 0)
            row["total_sisa"] = sum((bill.sisa_tagihan for bill in bills), 0)
            invoice_url = ""
            if bills:
                invoice_url = self.request.build_absolute_uri(
                    reverse("finance:bill_invoice_pdf", kwargs={"pk": bills[0].pk})
                )
            row["message"] = build_student_reminder_message(row["student"], bills, invoice_url=invoice_url)
            row["wa_url"] = build_whatsapp_url(row["student"].no_wa_wali, row["message"]) if row["student"].no_wa_wali else ""

        context["gateway"] = gateway
        context["templates"] = templates
        context["logs"] = logs
        context["student_rows"] = student_rows
        context["stats"] = {
            "pending_bills": pending_bills.count(),
            "pending_students": len(student_rows),
            "active_templates": templates.count(),
            "recent_logs": MessageLog.objects.count(),
            "gateway_active": bool(gateway),
        }
        return context


class WhatsAppGatewayListView(NotificationAdminRequiredMixin, ListView):
    model = WhatsAppGatewayConfig
    template_name = "notifications/gateway_list.html"
    context_object_name = "items"


class WhatsAppGatewayCreateView(NotificationAdminRequiredMixin, CreateView):
    model = WhatsAppGatewayConfig
    form_class = WhatsAppGatewayForm
    template_name = "notifications/form.html"
    success_url = reverse_lazy("notifications:gateway_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Gateway WhatsApp"
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Nama gateway dan endpoint API", "fields": ["name", "api_url"]},
            {"title": "Autentikasi", "hint": "Kunci API dan pengirim", "fields": ["api_key", "sender"]},
            {"title": "Status", "hint": "Aktifkan gateway yang dipakai", "fields": ["active"]},
        ]
        return context


class WhatsAppGatewayUpdateView(NotificationAdminRequiredMixin, UpdateView):
    model = WhatsAppGatewayConfig
    form_class = WhatsAppGatewayForm
    template_name = "notifications/form.html"
    success_url = reverse_lazy("notifications:gateway_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Gateway WhatsApp"
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Nama gateway dan endpoint API", "fields": ["name", "api_url"]},
            {"title": "Autentikasi", "hint": "Kunci API dan pengirim", "fields": ["api_key", "sender"]},
            {"title": "Status", "hint": "Aktifkan gateway yang dipakai", "fields": ["active"]},
        ]
        return context


class WhatsAppGatewayDeleteView(NotificationAdminRequiredMixin, DeleteView):
    model = WhatsAppGatewayConfig
    template_name = "notifications/confirm_delete.html"
    success_url = reverse_lazy("notifications:gateway_list")


class MessageTemplateListView(NotificationAdminRequiredMixin, ListView):
    model = MessageTemplate
    template_name = "notifications/template_list.html"
    context_object_name = "items"


class MessageTemplateCreateView(NotificationAdminRequiredMixin, CreateView):
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = "notifications/form.html"
    success_url = reverse_lazy("notifications:template_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Template Pesan"
        context["wizard_steps"] = [
            {"title": "Identitas", "hint": "Kode dan judul template", "fields": ["code", "title"]},
            {"title": "Isi Pesan", "hint": "Tulis isi pesan dengan placeholder", "fields": ["body"]},
            {"title": "Status", "hint": "Aktifkan template ini", "fields": ["active"]},
        ]
        return context


class MessageTemplateUpdateView(NotificationAdminRequiredMixin, UpdateView):
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = "notifications/form.html"
    success_url = reverse_lazy("notifications:template_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Template Pesan"
        context["wizard_steps"] = [
            {"title": "Identitas", "hint": "Kode dan judul template", "fields": ["code", "title"]},
            {"title": "Isi Pesan", "hint": "Tulis isi pesan dengan placeholder", "fields": ["body"]},
            {"title": "Status", "hint": "Aktifkan template ini", "fields": ["active"]},
        ]
        return context


class MessageTemplateDeleteView(NotificationAdminRequiredMixin, DeleteView):
    model = MessageTemplate
    template_name = "notifications/confirm_delete.html"
    success_url = reverse_lazy("notifications:template_list")


class SendBillReminderView(NotificationAdminRequiredMixin, View):
    def post(self, request, bill_id, *args, **kwargs):
        bill = get_object_or_404(Bill.objects.select_related("santri", "jenis_pembayaran"), pk=bill_id)
        number = bill.santri.no_wa_wali
        if not number:
            messages.error(request, "Nomor WhatsApp wali santri belum ada.")
            return redirect("finance:bill_list")

        invoice_url = request.build_absolute_uri(reverse("finance:bill_invoice_pdf", kwargs={"pk": bill.pk}))
        message = build_bill_reminder_message(bill, invoice_url=invoice_url)
        ok, response_text = send_whatsapp(number, message)
        MessageLog.objects.create(
            to_number=number,
            message=message,
            status="sent" if ok else "failed",
            response=response_text[:1000],
        )

        if ok:
            messages.success(request, f"Reminder WhatsApp untuk {bill.santri.nama_lengkap} berhasil dikirim.")
        else:
            messages.error(request, f"Gagal mengirim WhatsApp: {response_text}")
        return redirect("notifications:index")


class SendStudentReminderView(NotificationAdminRequiredMixin, View):
    def post(self, request, student_id, *args, **kwargs):
        bills = list(
            Bill.objects.filter(santri_id=student_id)
            .exclude(status=Bill.Status.LUNAS)
            .select_related("santri", "jenis_pembayaran")
            .order_by("periode_tahun", "periode_bulan")
        )
        if not bills:
            messages.info(request, "Tidak ada tagihan aktif untuk santri tersebut.")
            return redirect("notifications:index")

        student = bills[0].santri
        number = student.no_wa_wali
        if not number:
            messages.error(request, "Nomor WhatsApp wali santri belum ada.")
            return redirect("notifications:index")

        invoice_url = request.build_absolute_uri(reverse("finance:bill_invoice_pdf", kwargs={"pk": bills[0].pk}))
        message = build_student_reminder_message(student, bills, invoice_url=invoice_url)
        ok, response_text = send_whatsapp(number, message)
        MessageLog.objects.create(
            to_number=number,
            message=message,
            status="sent" if ok else "failed",
            response=response_text[:1000],
        )

        if ok:
            messages.success(request, f"Reminder WhatsApp untuk {student.nama_lengkap} berhasil dikirim.")
        else:
            messages.error(request, f"Gagal mengirim WhatsApp: {response_text}")
        return redirect("notifications:index")
