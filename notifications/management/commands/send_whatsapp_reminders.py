from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import WhatsAppReminderSchedule
from notifications.services import send_whatsapp, render_template
from finance.models import Bill


class Command(BaseCommand):
    help = "Kirim reminder WhatsApp berdasarkan tagihan yang belum lunas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Jalankan reminder tanpa memeriksa jam pengiriman.",
        )

    def handle(self, *args, **options):
        schedule = WhatsAppReminderSchedule.objects.first()
        if not schedule or not schedule.aktif:
            self.stdout.write(self.style.WARNING("Reminder belum diaktifkan."))
            return

        now = timezone.localtime(timezone.now())
        current_time = now.time().replace(second=0, microsecond=0)
        schedule_time = schedule.jam_kirim.replace(second=0, microsecond=0)

        if not options.get("force") and current_time != schedule_time:
            self.stdout.write(
                self.style.WARNING(
                    f"Bukan jam kirim reminder. Sekarang {current_time.strftime('%H:%M')}, jadwal {schedule_time.strftime('%H:%M')}."
                )
            )
            return

        if schedule.terakhir_dikirim_pada == now.date() and not options.get("force"):
            self.stdout.write(self.style.WARNING("Reminder sudah dijalankan hari ini."))
            return

        sent = 0
        for bill in Bill.objects.exclude(status=Bill.Status.LUNAS).select_related("santri", "jenis_pembayaran"):
            number = bill.santri.no_wa_wali
            if not number:
                continue
            message = render_template(
                "bill_reminder",
                {
                    "nama_santri": bill.santri.nama_lengkap,
                    "jenis_pembayaran": bill.jenis_pembayaran.nama,
                    "periode": f"{bill.periode_bulan}/{bill.periode_tahun}",
                    "nominal": bill.nominal,
                    "sisa_tagihan": bill.sisa_tagihan,
                    "jatuh_tempo": bill.jatuh_tempo,
                },
            ) or (
                f"Assalamu’alaikum Bapak/Ibu wali dari {bill.santri.nama_lengkap}.\n\n"
                f"Kami informasikan bahwa tagihan {bill.jenis_pembayaran.nama} periode {bill.periode_bulan}/{bill.periode_tahun} "
                f"sebesar Rp {bill.nominal} belum lunas.\n\n"
                f"Sisa tagihan: Rp {bill.sisa_tagihan}\n"
                f"Jatuh tempo: {bill.jatuh_tempo}\n\n"
                "Mohon segera melakukan pembayaran.\n\nBarakallahu fiikum."
            )
            ok, _ = send_whatsapp(number, message)
            sent += int(ok)
        schedule.terakhir_dikirim_pada = now.date()
        schedule.save(update_fields=["terakhir_dikirim_pada"])
        self.stdout.write(self.style.SUCCESS(f"Reminder terkirim: {sent}"))
