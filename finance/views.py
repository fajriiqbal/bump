from io import BytesIO

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView
from django.utils import timezone
from students.models import Student
from notifications.services import build_bill_reminder_message, build_whatsapp_url

from .forms import (
    BillForm,
    BillGenerateForm,
    BillListFilterForm,
    CashAccountForm,
    ExpenseForm,
    IncomeForm,
    PaymentCreateForm,
    PaymentForm,
    PaymentTypeForm,
    WhatsAppReminderScheduleForm,
)
from .models import Bill, CashAccount, Expense, Income, Payment, PaymentType, WhatsAppReminderSchedule
from .services import build_bill_invoice_pdf


class FinanceAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, "role", "") == "admin"


class FinanceWorkflowView(FinanceAdminRequiredMixin, TemplateView):
    template_name = "finance/workflow.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workflow_steps"] = [
            {
                "step": "1",
                "title": "Lengkapi Profil Pondok",
                "hint": "Pastikan nama pondok, alamat, kontak, dan kepala pesantren sudah diisi.",
                "actions": [
                    "Buka menu Profil Pondok",
                    "Lengkapi identitas resmi",
                    "Simpan sebagai data utama export dan invoice",
                ],
            },
            {
                "step": "2",
                "title": "Siapkan Jenis Pembayaran",
                "hint": "Buat master biaya yang akan dipakai untuk generate tagihan.",
                "actions": [
                    "Cek jenis pembayaran aktif",
                    "Pastikan nominal default benar",
                    "Aktifkan hanya item yang dipakai periode ini",
                ],
            },
            {
                "step": "3",
                "title": "Generate Tagihan",
                "hint": "Jalankan generate untuk semua santri aktif sesuai periode yang dipilih.",
                "actions": [
                    "Pilih bulan dan tahun tagihan",
                    "Klik Generate Tagihan",
                    "Cek apakah semua santri aktif sudah masuk",
                ],
            },
            {
                "step": "4",
                "title": "Review Tagihan Per Santri",
                "hint": "Gunakan halaman daftar tagihan untuk memastikan nominal, jatuh tempo, dan status.",
                "actions": [
                    "Cari nama santri jika diperlukan",
                    "Buka detail untuk melihat semua periode",
                    "Unduh invoice bila perlu dikirim ke wali",
                ],
            },
            {
                "step": "5",
                "title": "Kirim Reminder WhatsApp",
                "hint": "Gunakan reminder agar tagihan yang belum lunas tersampaikan secara teratur.",
                "actions": [
                    "Atur jam pengiriman reminder",
                    "Kirim reminder dari daftar tagihan",
                    "Pastikan link invoice ikut terbawa",
                ],
            },
            {
                "step": "6",
                "title": "Catat Pembayaran",
                "hint": "Setiap pembayaran masuk dicatat ke tagihan santri yang sesuai.",
                "actions": [
                    "Buka detail tagihan santri",
                    "Isi nominal dan metode pembayaran",
                    "Verifikasi pembayaran jika sudah dicek",
                ],
            },
            {
                "step": "7",
                "title": "Export Laporan",
                "hint": "Pakai PDF untuk arsip resmi, Excel untuk rekap dan analisis bendahara.",
                "actions": [
                    "Export PDF untuk dokumen formal",
                    "Export Excel untuk rekap data",
                    "Gunakan laporan per santri agar tidak dobel",
                ],
            },
            {
                "step": "8",
                "title": "Backup Rutin",
                "hint": "Simpan backup sebelum akhir bulan atau sebelum perubahan besar.",
                "actions": [
                    "Backup dulu sebelum restore atau update besar",
                    "Simpan file backup secara aman",
                    "Gunakan restore hanya jika benar-benar diperlukan",
                ],
            },
        ]
        context["quick_checks"] = [
            "Profil pondok sudah lengkap",
            "Jenis pembayaran aktif sudah benar",
            "Tagihan periode ini sudah digenerate",
            "Reminder dan export sudah siap",
        ]
        return context


class BillListView(FinanceAdminRequiredMixin, ListView):
    model = Bill
    template_name = "finance/bills/list.html"
    context_object_name = "bills"

    def get_queryset(self):
        queryset = Bill.objects.select_related("santri", "jenis_pembayaran").prefetch_related("payments").order_by(
            "santri__nama_lengkap",
            "periode_tahun",
            "periode_bulan",
            "id",
        )
        form = BillListFilterForm(self.request.GET or None)
        self.filter_form = form
        if form.is_valid():
            cleaned = form.cleaned_data
            q = cleaned.get("q")

            if q:
                queryset = queryset.filter(
                    Q(santri__nama_lengkap__icontains=q)
                    | Q(santri__nis__icontains=q)
                    | Q(santri__kelas__icontains=q)
                    | Q(santri__nama_wali__icontains=q)
                )
            return list(queryset)

        return list(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_rows = []
        bills = context["bills"]

        total_tagihan = sum((bill.total_tagihan for bill in bills), 0)
        total_dibayar = sum((bill.total_dibayar for bill in bills), 0)
        total_sisa = sum((bill.sisa_tagihan for bill in bills), 0)
        overdue_count = sum(1 for bill in bills if bill.is_overdue)
        paid_count = sum(1 for bill in bills if bill.effective_status == Bill.Status.LUNAS)
        student_count = len({bill.santri_id for bill in bills})

        grouped = {}
        ordered_students = []
        for bill in bills:
            if bill.santri_id not in grouped:
                grouped[bill.santri_id] = {
                    "student": bill.santri,
                    "bills": [],
                }
                ordered_students.append(grouped[bill.santri_id])
            grouped[bill.santri_id]["bills"].append(bill)

        for row in ordered_students:
            bills_for_student = row["bills"]
            latest_bill = bills_for_student[-1]
            unpaid_bills = [bill for bill in bills_for_student if bill.sisa_tagihan > 0]
            effective_statuses = [bill.effective_status for bill in bills_for_student]
            if all(status == Bill.Status.LUNAS for status in effective_statuses):
                status_label = "Lunas"
                status_class = "bg-emerald-100 text-emerald-700"
            elif any(status == Bill.Status.TERLAMBAT for status in effective_statuses):
                status_label = "Terlambat"
                status_class = "bg-red-100 text-red-700"
            elif any(status == Bill.Status.SEBAGIAN for status in effective_statuses):
                status_label = "Sebagian"
                status_class = "bg-amber-100 text-amber-700"
            else:
                status_label = "Belum Bayar"
                status_class = "bg-stone-100 text-stone-700"

            reminder_bill = unpaid_bills[-1] if unpaid_bills else latest_bill
            reminder_message = build_bill_reminder_message(reminder_bill) if reminder_bill else ""
            student_rows.append(
                {
                    "student": row["student"],
                    "bills": bills_for_student,
                    "bill_count": len(bills_for_student),
                    "total_tagihan": sum((bill.total_tagihan for bill in bills_for_student), 0),
                    "total_dibayar": sum((bill.total_dibayar for bill in bills_for_student), 0),
                    "total_sisa": sum((bill.sisa_tagihan for bill in bills_for_student), 0),
                    "latest_bill": latest_bill,
                    "latest_bill_label": f"{latest_bill.jenis_pembayaran.nama} - {latest_bill.periode_bulan}/{latest_bill.periode_tahun}",
                    "latest_bill_status": latest_bill.effective_status_label,
                    "latest_bill_due": latest_bill.jatuh_tempo,
                    "status_label": status_label,
                    "status_class": status_class,
                    "reminder_bill": reminder_bill,
                    "reminder_message": reminder_message,
                    "wa_url": build_whatsapp_url(row["student"].no_wa_wali, reminder_message) if row["student"].no_wa_wali and unpaid_bills else "",
                }
            )

        context["student_rows"] = student_rows
        context["summary"] = {
            "bill_count": len(bills),
            "student_count": student_count,
            "paid_count": paid_count,
            "overdue_count": overdue_count,
            "total_tagihan": total_tagihan,
            "total_dibayar": total_dibayar,
            "total_sisa": total_sisa,
        }
        context["filter_form"] = self.filter_form
        return context


class BillStudentDetailView(FinanceAdminRequiredMixin, DetailView):
    model = Student
    template_name = "finance/bills/detail.html"
    context_object_name = "student"

    def get_queryset(self):
        return Student.objects.prefetch_related(
            Prefetch(
                "bills",
                queryset=Bill.objects.select_related("jenis_pembayaran").prefetch_related("payments__diterima_oleh").order_by(
                    "periode_tahun", "periode_bulan", "id"
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bills = list(self.object.bills.all())
        payments = []
        for bill in bills:
            for payment in bill.payments.all():
                payments.append(payment)

        payments.sort(key=lambda payment: (payment.tanggal_bayar, payment.id), reverse=True)

        total_tagihan = sum((bill.total_tagihan for bill in bills), 0)
        total_dibayar = sum((bill.total_dibayar for bill in bills), 0)
        total_sisa = sum((bill.sisa_tagihan for bill in bills), 0)
        paid_bills = sum(1 for bill in bills if bill.effective_status == Bill.Status.LUNAS)

        context["bills"] = bills
        context["payments"] = payments
        context["summary"] = {
            "bill_count": len(bills),
            "paid_bills": paid_bills,
            "open_bills": len(bills) - paid_bills,
            "total_tagihan": total_tagihan,
            "total_dibayar": total_dibayar,
            "total_sisa": total_sisa,
        }
        return context


class BillInvoicePdfView(FinanceAdminRequiredMixin, DetailView):
    model = Bill

    def get_queryset(self):
        return Bill.objects.select_related("santri", "jenis_pembayaran").prefetch_related("payments__diterima_oleh")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        pdf_bytes = build_bill_invoice_pdf(self.object)
        filename = f"invoice-{self.object.santri.nis}-{self.object.periode_bulan:02d}{self.object.periode_tahun}.pdf"
        response = FileResponse(
            BytesIO(pdf_bytes),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class BillGenerateView(FinanceAdminRequiredMixin, FormView):
    template_name = "finance/bills/generate.html"
    form_class = BillGenerateForm
    success_url = reverse_lazy("finance:bill_list")

    def form_valid(self, form):
        payment_type = form.cleaned_data["payment_type"]
        period_month = int(form.cleaned_data["periode_bulan"])
        period_year = form.cleaned_data["periode_tahun"]

        students = Student.objects.filter(status=Student.Status.AKTIF)

        if not students.exists():
            messages.info(self.request, "Tidak ada santri yang cocok untuk digenerate pada periode ini.")
            return super().form_valid(form)

        created = 0
        skipped = 0

        with transaction.atomic():
            for student in students:
                bill, was_created = Bill.objects.get_or_create(
                    santri=student,
                    jenis_pembayaran=payment_type,
                    periode_bulan=period_month,
                    periode_tahun=period_year,
                    defaults={
                        "nominal": payment_type.nominal_default,
                        "diskon": 0,
                        "denda": 0,
                    },
                )
                if was_created:
                    bill.nominal = payment_type.nominal_default
                    bill.diskon = 0
                    bill.denda = 0
                    bill.jatuh_tempo = bill.default_jatuh_tempo()
                    bill.recalculate()
                    bill.save()
                    created += 1
                else:
                    skipped += 1

        messages.success(
            self.request,
            f"Generate selesai: {created} tagihan baru dibuat, {skipped} sudah ada sebelumnya.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Periode", "hint": "Pilih bulan dan tahun tagihan", "fields": ["periode_bulan", "periode_tahun"]},
            {"title": "Jenis", "hint": "Tentukan jenis pembayaran", "fields": ["payment_type"]},
        ]
        return context


class PaymentListView(FinanceAdminRequiredMixin, ListView):
    model = Payment
    template_name = "finance/payments/list.html"
    context_object_name = "payments"

    def get_queryset(self):
        return Payment.objects.select_related("bill", "santri", "bill__jenis_pembayaran", "diterima_oleh").order_by("-tanggal_bayar", "-id")


class PaymentCreateView(FinanceAdminRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentCreateForm
    template_name = "finance/payments/form.html"
    success_url = reverse_lazy("finance:bill_list")

    def dispatch(self, request, *args, **kwargs):
        self.bill = get_object_or_404(
            Bill.objects.select_related("santri", "jenis_pembayaran"),
            pk=kwargs["bill_id"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["bill"] = self.bill
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["verified"] = False
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bill"] = self.bill
        context["wizard_steps"] = [
            {"title": "Pembayaran", "hint": "Isi nominal dan metode", "fields": ["jumlah_bayar", "metode_bayar", "bukti_transfer", "verified"]},
            {"title": "Catatan", "hint": "Tambahan informasi transaksi", "fields": ["catatan"]},
        ]
        return context

    def form_valid(self, form):
        payment = form.save(commit=False)
        payment.bill = self.bill
        payment.santri = self.bill.santri
        payment.diterima_oleh = self.request.user

        if payment.jumlah_bayar is None:
            payment.jumlah_bayar = self.bill.sisa_tagihan

        payment.save()

        total_paid = Payment.objects.filter(bill=self.bill).aggregate(total=Sum("jumlah_bayar")).get("total") or 0
        self.bill.total_dibayar = total_paid
        self.bill.recalculate()
        self.bill.save(update_fields=["total_dibayar", "sisa_tagihan", "status"])

        messages.success(self.request, f"Pembayaran untuk {self.bill.santri.nama_lengkap} berhasil disimpan.")
        self.object = payment
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("finance:bill_student_detail", kwargs={"pk": self.bill.santri_id})


class PaymentTypeListView(FinanceAdminRequiredMixin, ListView):
    model = PaymentType
    template_name = "finance/payment_types/list.html"
    context_object_name = "items"


class PaymentTypeCreateView(FinanceAdminRequiredMixin, CreateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:payment_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Identitas jenis", "fields": ["nama", "kategori", "tipe"]},
            {"title": "Aturan", "hint": "Nominal dan denda", "fields": ["nominal_default", "denda_per_hari", "wajib", "aktif"]},
            {"title": "Catatan", "hint": "Deskripsi tambahan", "fields": ["deskripsi"]},
        ]
        return context


class PaymentTypeUpdateView(FinanceAdminRequiredMixin, UpdateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:payment_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Identitas jenis", "fields": ["nama", "kategori", "tipe"]},
            {"title": "Aturan", "hint": "Nominal dan denda", "fields": ["nominal_default", "denda_per_hari", "wajib", "aktif"]},
            {"title": "Catatan", "hint": "Deskripsi tambahan", "fields": ["deskripsi"]},
        ]
        return context


class PaymentTypeDeleteView(FinanceAdminRequiredMixin, DeleteView):
    model = PaymentType
    template_name = "finance/confirm_delete.html"
    success_url = reverse_lazy("finance:payment_type_list")


class WhatsAppReminderScheduleView(FinanceAdminRequiredMixin, UpdateView):
    model = WhatsAppReminderSchedule
    form_class = WhatsAppReminderScheduleForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:bill_list")

    def get_object(self, queryset=None):
        schedule, _ = WhatsAppReminderSchedule.objects.get_or_create(
            pk=1,
            defaults={
                "nama": "Reminder Tagihan",
                "aktif": False,
            },
        )
        return schedule

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Pengaturan Reminder"
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Nama pengaturan reminder", "fields": ["nama"]},
            {"title": "Waktu", "hint": "Atur jam pengiriman reminder", "fields": ["jam_kirim", "aktif"]},
            {"title": "Catatan", "hint": "Tambahkan keterangan opsional", "fields": ["catatan"]},
        ]
        return context


class CashAccountListView(FinanceAdminRequiredMixin, ListView):
    model = CashAccount
    template_name = "finance/cash_accounts/list.html"
    context_object_name = "items"


class CashAccountCreateView(FinanceAdminRequiredMixin, CreateView):
    model = CashAccount
    form_class = CashAccountForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:cash_account_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Identitas kas", "fields": ["nama", "saldo_awal"]},
            {"title": "Status", "hint": "Aktivitas akun", "fields": ["aktif"]},
        ]
        return context


class CashAccountUpdateView(FinanceAdminRequiredMixin, UpdateView):
    model = CashAccount
    form_class = CashAccountForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:cash_account_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Identitas kas", "fields": ["nama", "saldo_awal"]},
            {"title": "Status", "hint": "Aktivitas akun", "fields": ["aktif"]},
        ]
        return context


class CashAccountDeleteView(FinanceAdminRequiredMixin, DeleteView):
    model = CashAccount
    template_name = "finance/confirm_delete.html"
    success_url = reverse_lazy("finance:cash_account_list")


class IncomeListView(FinanceAdminRequiredMixin, ListView):
    model = Income
    template_name = "finance/income/list.html"
    context_object_name = "items"


class IncomeCreateView(FinanceAdminRequiredMixin, CreateView):
    model = Income
    form_class = IncomeForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:income_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Sumber pemasukan", "fields": ["akun", "kategori", "sumber"]},
            {"title": "Nominal", "hint": "Nilai transaksi", "fields": ["nominal"]},
            {"title": "Catatan", "hint": "Bukti dan keterangan", "fields": ["bukti", "catatan"]},
        ]
        return context


class IncomeUpdateView(FinanceAdminRequiredMixin, UpdateView):
    model = Income
    form_class = IncomeForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:income_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Sumber pemasukan", "fields": ["akun", "kategori", "sumber"]},
            {"title": "Nominal", "hint": "Nilai transaksi", "fields": ["nominal"]},
            {"title": "Catatan", "hint": "Bukti dan keterangan", "fields": ["bukti", "catatan"]},
        ]
        return context


class IncomeDeleteView(FinanceAdminRequiredMixin, DeleteView):
    model = Income
    template_name = "finance/confirm_delete.html"
    success_url = reverse_lazy("finance:income_list")


class ExpenseListView(FinanceAdminRequiredMixin, ListView):
    model = Expense
    template_name = "finance/expense/list.html"
    context_object_name = "items"


class ExpenseCreateView(FinanceAdminRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:expense_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Sumber pengeluaran", "fields": ["akun", "kategori"]},
            {"title": "Nominal", "hint": "Nilai transaksi", "fields": ["nominal", "status", "approved_by"]},
            {"title": "Catatan", "hint": "Bukti dan keterangan", "fields": ["bukti", "catatan"]},
        ]
        return context


class ExpenseUpdateView(FinanceAdminRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/form.html"
    success_url = reverse_lazy("finance:expense_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wizard_steps"] = [
            {"title": "Dasar", "hint": "Sumber pengeluaran", "fields": ["akun", "kategori"]},
            {"title": "Nominal", "hint": "Nilai transaksi", "fields": ["nominal", "status", "approved_by"]},
            {"title": "Catatan", "hint": "Bukti dan keterangan", "fields": ["bukti", "catatan"]},
        ]
        return context


class ExpenseDeleteView(FinanceAdminRequiredMixin, DeleteView):
    model = Expense
    template_name = "finance/confirm_delete.html"
    success_url = reverse_lazy("finance:expense_list")
