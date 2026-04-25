from django.urls import path
from .views import ReportIndexView, export_bills_pdf, export_bills_xlsx, export_cash_pdf, export_payments_csv

app_name = "reports"

urlpatterns = [
    path("", ReportIndexView.as_view(), name="index"),
    path("bills.pdf", export_bills_pdf, name="export_bills_pdf"),
    path("payments.csv", export_payments_csv, name="export_payments_csv"),
    path("bills.xlsx", export_bills_xlsx, name="export_bills_xlsx"),
    path("cash.pdf", export_cash_pdf, name="export_cash_pdf"),
]
