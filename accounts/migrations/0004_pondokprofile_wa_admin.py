# Generated manually to add admin WhatsApp contact to PondokProfile.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_pondokprofile_bank_atas_nama_pondokprofile_bank_nama_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="pondokprofile",
            name="wa_admin",
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
