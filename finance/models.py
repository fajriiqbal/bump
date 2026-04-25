from decimal import Decimal
from datetime import date, timedelta, time
from calendar import monthrange
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone
from students.models import Student


class PaymentType(models.Model):
    class Type(models.TextChoices):
        BULANAN = "bulanan", "Bulanan"
        TAHUNAN = "tahunan", "Tahunan"
        SEKALI = "sekali_bayar", "Sekali Bayar"

    nama = models.CharField(max_length=150)
    kategori = models.CharField(max_length=100)
    nominal_default = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tipe = models.CharField(max_length=20, choices=Type.choices)
    wajib = models.BooleanField(default=True)
    aktif = models.BooleanField(default=True)
    denda_per_hari = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deskripsi = models.TextField(blank=True)

    def __str__(self):
        return self.nama


class Bill(models.Model):
    class Status(models.TextChoices):
        BELUM = "belum_bayar", "Belum Bayar"
        SEBAGIAN = "sebagian", "Sebagian"
        LUNAS = "lunas", "Lunas"
        TERLAMBAT = "terlambat", "Terlambat"

    santri = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="bills")
    jenis_pembayaran = models.ForeignKey(PaymentType, on_delete=models.PROTECT)
    periode_bulan = models.PositiveSmallIntegerField(default=1)
    periode_tahun = models.PositiveSmallIntegerField(default=2026)
    nominal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    diskon = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    denda = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tagihan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_dibayar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sisa_tagihan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    jatuh_tempo = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BELUM)
    created_at = models.DateTimeField(auto_now_add=True)

    def default_jatuh_tempo(self):
        last_day = monthrange(self.periode_tahun, self.periode_bulan)[1]
        month_end = date(self.periode_tahun, self.periode_bulan, last_day)
        return month_end - timedelta(days=7)

    def recalculate(self):
        self.total_tagihan = max((self.nominal - self.diskon) + self.denda, Decimal("0"))
        self.sisa_tagihan = max(self.total_tagihan - self.total_dibayar, Decimal("0"))
        if not self.jatuh_tempo:
            self.jatuh_tempo = self.default_jatuh_tempo()
        if self.sisa_tagihan <= 0:
            self.status = self.Status.LUNAS
            return

        if self.total_dibayar <= 0:
            self.status = self.Status.BELUM
        elif self.jatuh_tempo and self.jatuh_tempo < timezone.localdate():
            self.status = self.Status.TERLAMBAT
        else:
            self.status = self.Status.SEBAGIAN

    @property
    def is_overdue(self):
        return self.sisa_tagihan > 0 and self.jatuh_tempo and self.jatuh_tempo < timezone.localdate()

    @property
    def effective_status(self):
        if self.sisa_tagihan <= 0:
            return self.Status.LUNAS
        if self.is_overdue:
            return self.Status.TERLAMBAT
        if self.total_dibayar <= 0:
            return self.Status.BELUM
        return self.Status.SEBAGIAN

    @property
    def effective_status_label(self):
        return self.Status(self.effective_status).label

    def __str__(self):
        return f"{self.santri} - {self.jenis_pembayaran}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        TRANSFER = "transfer", "Transfer"
        QRIS = "qris", "QRIS"

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    santri = models.ForeignKey(Student, on_delete=models.CASCADE)
    tanggal_bayar = models.DateField(auto_now_add=True)
    jumlah_bayar = models.DecimalField(max_digits=12, decimal_places=2)
    metode_bayar = models.CharField(max_length=20, choices=Method.choices)
    bukti_transfer = models.ImageField(upload_to="payments/", blank=True, null=True)
    nomor_transaksi = models.CharField(max_length=50, unique=True, editable=False)
    diterima_oleh = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    catatan = models.TextField(blank=True)
    verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.nomor_transaksi:
            tanggal = self.tanggal_bayar or timezone.now().date()
            suffix = uuid4().hex[:8].upper()
            self.nomor_transaksi = f"PAY-{self.bill_id}-{self.santri_id}-{tanggal:%Y%m%d}-{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nomor_transaksi


class CashAccount(models.Model):
    nama = models.CharField(max_length=100)
    saldo_awal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    aktif = models.BooleanField(default=True)

    def __str__(self):
        return self.nama


class Income(models.Model):
    akun = models.ForeignKey(CashAccount, on_delete=models.PROTECT)
    kategori = models.CharField(max_length=100)
    sumber = models.CharField(max_length=150)
    nominal = models.DecimalField(max_digits=12, decimal_places=2)
    tanggal = models.DateField(auto_now_add=True)
    bukti = models.FileField(upload_to="income/", blank=True, null=True)
    catatan = models.TextField(blank=True)


class Expense(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    akun = models.ForeignKey(CashAccount, on_delete=models.PROTECT)
    kategori = models.CharField(max_length=100)
    nominal = models.DecimalField(max_digits=12, decimal_places=2)
    tanggal = models.DateField(auto_now_add=True)
    bukti = models.FileField(upload_to="expense/", blank=True, null=True)
    catatan = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)


class WhatsAppReminderSchedule(models.Model):
    nama = models.CharField(max_length=100, default="Reminder Tagihan")
    aktif = models.BooleanField(default=False)
    jam_kirim = models.TimeField(default=time(8, 0))
    terakhir_dikirim_pada = models.DateField(null=True, blank=True)
    catatan = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nama} - {self.jam_kirim}"
