from datetime import date

from django import forms
from .models import Bill, Payment, PaymentType, Income, Expense, CashAccount, WhatsAppReminderSchedule


MONTH_CHOICES = [
    (1, "Januari"),
    (2, "Februari"),
    (3, "Maret"),
    (4, "April"),
    (5, "Mei"),
    (6, "Juni"),
    (7, "Juli"),
    (8, "Agustus"),
    (9, "September"),
    (10, "Oktober"),
    (11, "November"),
    (12, "Desember"),
]


class StyledFinanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            input_type = getattr(widget, "input_type", "")
            if input_type in {"checkbox", "radio"}:
                widget.attrs["class"] = "h-4 w-4 rounded border-stone-300 text-brown-primary focus:ring-gold-soft"
            elif input_type == "file":
                widget.attrs["class"] = "block w-full appearance-none border-0 bg-transparent px-0 py-3 text-sm text-brown-dark file:mr-4 file:rounded-xl file:border-0 file:bg-cream file:px-4 file:py-2 file:text-brown-dark"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = "input-modern pr-8"
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = "input-modern min-h-[140px]"
            else:
                current = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{current} input-modern".strip()


class PaymentTypeForm(StyledFinanceForm):
    class Meta:
        model = PaymentType
        fields = "__all__"


class BillForm(StyledFinanceForm):
    class Meta:
        model = Bill
        fields = "__all__"


class PaymentForm(StyledFinanceForm):
    class Meta:
        model = Payment
        fields = ["bill", "santri", "jumlah_bayar", "metode_bayar", "bukti_transfer", "catatan", "diterima_oleh"]


class PaymentCreateForm(StyledFinanceForm):
    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop("bill", None)
        super().__init__(*args, **kwargs)
        if self.bill and not self.is_bound:
            self.fields["jumlah_bayar"].initial = self.bill.sisa_tagihan
        if self.bill:
            self.fields["verified"].initial = False
            self.fields["jumlah_bayar"].help_text = f"Maksimal {self.bill.sisa_tagihan} sesuai sisa tagihan."

    class Meta:
        model = Payment
        fields = ["jumlah_bayar", "metode_bayar", "bukti_transfer", "catatan", "verified"]

    def clean_jumlah_bayar(self):
        amount = self.cleaned_data["jumlah_bayar"]
        if amount <= 0:
            raise forms.ValidationError("Jumlah bayar harus lebih dari 0.")
        if self.bill and amount > self.bill.sisa_tagihan:
            raise forms.ValidationError("Jumlah bayar tidak boleh melebihi sisa tagihan.")
        return amount


class CashAccountForm(StyledFinanceForm):
    class Meta:
        model = CashAccount
        fields = "__all__"


class IncomeForm(StyledFinanceForm):
    class Meta:
        model = Income
        fields = "__all__"


class ExpenseForm(StyledFinanceForm):
    class Meta:
        model = Expense
        fields = "__all__"


class WhatsAppReminderScheduleForm(StyledFinanceForm):
    class Meta:
        model = WhatsAppReminderSchedule
        fields = ["nama", "aktif", "jam_kirim", "catatan"]
        widgets = {
            "jam_kirim": forms.TimeInput(attrs={"type": "time"}),
        }


class BillGenerateForm(forms.Form):
    payment_type = forms.ModelChoiceField(
        label="Jenis Pembayaran",
        queryset=PaymentType.objects.filter(aktif=True),
        help_text="Pilih jenis pembayaran yang akan digenerate menjadi tagihan.",
    )
    periode_bulan = forms.ChoiceField(
        label="Bulan Periode",
        choices=MONTH_CHOICES,
        initial=date.today().month,
    )
    periode_tahun = forms.IntegerField(
        label="Tahun Periode",
        initial=date.today().year,
        min_value=2000,
        max_value=2100,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_type"].queryset = PaymentType.objects.filter(aktif=True).order_by("nama")


class BillListFilterForm(forms.Form):
    q = forms.CharField(
        label="Cari santri",
        required=False,
        help_text="Cari berdasarkan nama, NIS, kelas, atau wali.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].widget.attrs.update(
            {
                "placeholder": "Cari nama, NIS, kelas, atau wali",
                "class": "input-modern h-11",
                "autocomplete": "off",
            }
        )
