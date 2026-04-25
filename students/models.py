from django.db import models


class Student(models.Model):
    class Gender(models.TextChoices):
        LAKI = "L", "Laki-laki"
        PEREMPUAN = "P", "Perempuan"

    class Status(models.TextChoices):
        AKTIF = "aktif", "Aktif"
        NONAKTIF = "nonaktif", "Nonaktif"
        ALUMNI = "alumni", "Alumni"

    nis = models.CharField(max_length=50, unique=True)
    nama_lengkap = models.CharField(max_length=150)
    jenis_kelamin = models.CharField(max_length=1, choices=Gender.choices)
    tempat_lahir = models.CharField(max_length=100, blank=True)
    tanggal_lahir = models.DateField(null=True, blank=True)
    alamat = models.TextField(blank=True)
    nama_ayah = models.CharField(max_length=150, blank=True)
    nama_ibu = models.CharField(max_length=150, blank=True)
    nama_wali = models.CharField(max_length=150, blank=True)
    no_wa_wali = models.CharField(max_length=20, blank=True)
    kelas = models.CharField(max_length=100, blank=True)
    kamar = models.CharField(max_length=100, blank=True)
    tanggal_masuk = models.DateField(null=True, blank=True)
    tahun_ajaran = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AKTIF)
    foto = models.ImageField(upload_to="students/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nama_lengkap"]

    def __str__(self):
        return f"{self.nis} - {self.nama_lengkap}"
