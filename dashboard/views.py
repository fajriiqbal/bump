import json
from calendar import month_name

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from students.models import Student
from finance.models import Bill, CashAccount, Income, Expense, Payment


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/home.html"

    def get(self, request):
        current_year = timezone.now().year
        today = timezone.localdate()
        monthly_income = Income.objects.filter(tanggal__year=current_year).aggregate(total=Sum("nominal")).get("total") or 0
        monthly_expense = Expense.objects.filter(tanggal__year=current_year).aggregate(total=Sum("nominal")).get("total") or 0
        total_bills = Bill.objects.aggregate(total=Sum("total_tagihan")).get("total") or 0
        total_students = Student.objects.count()
        unpaid_bills = Bill.objects.filter(sisa_tagihan__gt=0)
        overdue_bills = Bill.objects.filter(sisa_tagihan__gt=0, jatuh_tempo__lt=today)
        stats = {
            "active_students": Student.objects.filter(status=Student.Status.AKTIF).count(),
            "total_students": total_students,
            "pending_bills": unpaid_bills.count(),
            "overdue_bills": overdue_bills.count(),
            "monthly_bills": total_bills,
            "monthly_payments": Payment.objects.filter(tanggal_bayar__year=current_year).aggregate(total=Sum("jumlah_bayar")).get("total") or 0,
            "cash_balance": (CashAccount.objects.aggregate(total=Sum("saldo_awal")).get("total") or 0)
                            + monthly_income - monthly_expense,
        }
        overdue_students = (
            Student.objects.filter(bills__sisa_tagihan__gt=0, bills__jatuh_tempo__lt=today)
            .distinct()
            .order_by("nama_lengkap")[:8]
        )

        income_by_month = {
            row["month"].month: float(row["total"] or 0)
            for row in Income.objects.filter(tanggal__year=current_year)
            .annotate(month=TruncMonth("tanggal"))
            .values("month")
            .annotate(total=Sum("nominal"))
        }
        expense_by_month = {
            row["month"].month: float(row["total"] or 0)
            for row in Expense.objects.filter(tanggal__year=current_year)
            .annotate(month=TruncMonth("tanggal"))
            .values("month")
            .annotate(total=Sum("nominal"))
        }
        payment_by_month = {
            row["month"].month: float(row["total"] or 0)
            for row in Payment.objects.filter(tanggal_bayar__year=current_year)
            .annotate(month=TruncMonth("tanggal_bayar"))
            .values("month")
            .annotate(total=Sum("jumlah_bayar"))
        }
        chart_labels = [month_name[i][:3] for i in range(1, 13)]
        income_series = [income_by_month.get(i, 0.0) for i in range(1, 13)]
        expense_series = [expense_by_month.get(i, 0.0) for i in range(1, 13)]
        payment_series = [payment_by_month.get(i, 0.0) for i in range(1, 13)]
        recent_payments = Payment.objects.select_related("santri", "bill__jenis_pembayaran", "diterima_oleh").order_by("-tanggal_bayar", "-id")[:5]
        recent_bills = unpaid_bills.select_related("santri", "jenis_pembayaran").order_by("-created_at", "-id")[:5]
        return render(request, self.template_name, {
            "stats": stats,
            "overdue_students": overdue_students,
            "recent_payments": recent_payments,
            "recent_bills": recent_bills,
            "chart_labels": json.dumps(chart_labels),
            "income_series": json.dumps(income_series),
            "expense_series": json.dumps(expense_series),
            "payment_series": json.dumps(payment_series),
            "current_year": current_year,
        })
