from datetime import time

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppReminderSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nama", models.CharField(default="Reminder Tagihan", max_length=100)),
                ("aktif", models.BooleanField(default=False)),
                ("jam_kirim", models.TimeField(default=time(8, 0))),
                ("terakhir_dikirim_pada", models.DateField(blank=True, null=True)),
                ("catatan", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
