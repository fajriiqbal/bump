import csv

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import TemplateView
from accounts.decorators import admin_required
from finance.models import Payment

from .services import build_bills_pdf, build_bills_workbook


class StaffReportAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, "role", "") in {"admin", "pengasuh"}


class ReportIndexView(StaffReportAccessMixin, TemplateView):
    template_name = "reports/index.html"


@admin_required
def export_payments_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="laporan_pembayaran.csv"'
    writer = csv.writer(response)
    writer.writerow(["Nomor Transaksi", "Santri", "Jumlah", "Metode"])
    for item in Payment.objects.select_related("santri"):
        writer.writerow([item.nomor_transaksi, item.santri.nama_lengkap, item.jumlah_bayar, item.metode_bayar])
    return response


@admin_required
def export_bills_xlsx(request):
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="laporan_tagihan.xlsx"'
    response.write(build_bills_workbook())
    return response


@admin_required
def export_bills_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="laporan_tagihan.pdf"'
    response.write(build_bills_pdf())
    return response


@admin_required
def export_cash_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="laporan_kas.pdf"'
    response.write(b"%PDF-1.4\n% Minimal placeholder PDF export.\n")
    return response
