from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.utils import OperationalError, ProgrammingError


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin / Bendahara"
        PENGASUH = "pengasuh", "Pengasuh"
        WALI = "wali", "Santri / Wali Santri"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WALI)
    phone = models.CharField(max_length=20, blank=True)

    def is_finance_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def display_role(self):
        if self.is_superuser or self.role == self.Role.ADMIN:
            return self.Role.ADMIN.label
        return self.get_role_display()


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.object_type}"


class PondokProfile(models.Model):
    nama_pondok = models.CharField(max_length=150, blank=True)
    alamat = models.CharField(max_length=255, blank=True)
    kota = models.CharField(max_length=100, blank=True)
    telepon = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    kepala_pesantren = models.CharField(max_length=150, blank=True)
    bendahara_nama = models.CharField(max_length=150, blank=True)
    bendahara_telepon = models.CharField(max_length=30, blank=True)
    wa_admin = models.CharField(max_length=30, blank=True)
    bank_nama = models.CharField(max_length=100, blank=True)
    bank_nomor_rekening = models.CharField(max_length=50, blank=True)
    bank_atas_nama = models.CharField(max_length=150, blank=True)
    qris_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    motto = models.CharField(max_length=255, blank=True)
    catatan = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Pondok"
        verbose_name_plural = "Profil Pondok"

    @classmethod
    def get_solo(cls):
        try:
            profile, _ = cls.objects.get_or_create(pk=1)
            return profile
        except (OperationalError, ProgrammingError):
            return cls(pk=1)

    def is_complete(self):
        required_fields = [
            self.nama_pondok,
            self.alamat,
            self.kota,
            self.telepon,
            self.kepala_pesantren,
        ]
        return all(value.strip() for value in required_fields)

    @property
    def display_name(self):
        return self.nama_pondok.strip() or "Pondok Pesantren"

    @property
    def display_address(self):
        parts = [part.strip() for part in [self.alamat, self.kota] if part and part.strip()]
        return ", ".join(parts)

    @property
    def initials(self):
        source = self.nama_pondok.strip() or "PP"
        words = [word for word in source.split() if word]
        if not words:
            return "PP"
        letters = "".join(word[0] for word in words[:2]).upper()
        return letters or "PP"

    def __str__(self):
        return self.display_name
