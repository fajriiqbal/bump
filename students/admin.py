from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("nis", "nama_lengkap", "kelas", "kamar", "status")
    search_fields = ("nis", "nama_lengkap", "nama_wali")
    list_filter = ("status", "kelas", "tahun_ajaran")
