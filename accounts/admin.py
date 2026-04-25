from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AuditLog, PondokProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role", "phone")}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "object_type", "object_id", "actor", "created_at")
    search_fields = ("action", "object_type", "object_id", "actor__username")


@admin.register(PondokProfile)
class PondokProfileAdmin(admin.ModelAdmin):
    list_display = ("nama_pondok", "kota", "telepon", "bendahara_nama", "wa_admin", "updated_at")
    fieldsets = (
        ("Identitas", {"fields": ("nama_pondok", "motto")}),
        ("Alamat", {"fields": ("alamat", "kota", "telepon", "email", "website")}),
        ("Penanggung Jawab", {"fields": ("kepala_pesantren", "bendahara_nama", "bendahara_telepon", "wa_admin")}),
        ("Pembayaran", {"fields": ("bank_nama", "bank_nomor_rekening", "bank_atas_nama", "qris_url")}),
        ("Catatan", {"fields": ("catatan",)}),
    )
