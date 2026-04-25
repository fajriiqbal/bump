from datetime import date

from django.db import migrations


def set_default_due_dates(apps, schema_editor):
    Bill = apps.get_model("finance", "Bill")
    for bill in Bill.objects.filter(jatuh_tempo__isnull=True):
        due_month = bill.periode_bulan + 1
        due_year = bill.periode_tahun
        if due_month > 12:
            due_month = 1
            due_year += 1
        bill.jatuh_tempo = date(due_year, due_month, 10)
        bill.save(update_fields=["jatuh_tempo"])


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0002_whatsappreminderschedule"),
    ]

    operations = [
        migrations.RunPython(set_default_due_dates, migrations.RunPython.noop),
    ]
