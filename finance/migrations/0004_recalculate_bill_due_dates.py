from calendar import monthrange
from datetime import date, timedelta

from django.db import migrations


def set_due_dates_to_month_end_minus_week(apps, schema_editor):
    Bill = apps.get_model("finance", "Bill")
    for bill in Bill.objects.all():
        last_day = monthrange(bill.periode_tahun, bill.periode_bulan)[1]
        month_end = date(bill.periode_tahun, bill.periode_bulan, last_day)
        bill.jatuh_tempo = month_end - timedelta(days=7)
        bill.save(update_fields=["jatuh_tempo"])


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0003_backfill_bill_due_dates"),
    ]

    operations = [
        migrations.RunPython(set_due_dates_to_month_end_minus_week, migrations.RunPython.noop),
    ]
