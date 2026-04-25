from decimal import Decimal
from urllib.parse import quote

from django.template import Context, Template

from accounts.models import PondokProfile
from .models import MessageTemplate, WhatsAppGatewayConfig


MONTH_NAMES = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def render_template(code, context):
    template = MessageTemplate.objects.filter(code=code, active=True).first()
    if not template:
        return ""
    return Template(template.body).render(Context(context))


def send_whatsapp(to_number, message):
    import requests

    gateway = WhatsAppGatewayConfig.objects.filter(active=True).first()
    if not gateway:
        return False, "Gateway belum dikonfigurasi"
    payload = {"target": to_number, "message": message, "countryCode": "62"}
    headers = {"Authorization": gateway.api_key}
    try:
        response = requests.post(gateway.api_url, json=payload, headers=headers, timeout=30)
        ok = response.status_code < 400
        return ok, response.text
    except Exception as exc:
        return False, str(exc)


def format_rupiah(value):
    try:
        amount = Decimal(value or 0)
    except Exception:
        amount = Decimal("0")
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"Rp {formatted}"


def normalize_phone_number(number):
    digits = "".join(ch for ch in str(number or "") if ch.isdigit())
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    return digits


def format_period_label(bill):
    month = MONTH_NAMES.get(int(bill.periode_bulan), str(bill.periode_bulan))
    return f"{month} {bill.periode_tahun}"


def format_bill_status(bill):
    if bill.is_overdue:
        return "Terlambat"
    if bill.total_dibayar <= 0:
        return "Belum terbayar"
    if bill.sisa_tagihan > 0:
        return "Terbayar sebagian"
    return bill.effective_status_label


def build_payment_footer(profile):
    pondok_name = profile.nama_pondok if profile and profile.nama_pondok else "sistem"
    return "\n".join(
        [
            "Jazakumullahu khairan. Wassalamu'alaikum warahmatullahi wabarakatuh.",
            "____________________________",
            "",
            (
                "Catatan: _Pesan ini tidak perlu dibalas karena dikirim otomatis oleh "
                f"sistem keuangan digital *{pondok_name}* sebagai pengingat tagihan santri yang belum lunas. "
                "Untuk pertanyaan dan konfirmasi dapat hubungi kontak di atas._"
            ),
        ]
    )


def build_reminder_message(student, bills, invoice_url=None):
    profile = PondokProfile.get_solo()
    bills = sorted(list(bills), key=lambda bill: (bill.periode_tahun, bill.periode_bulan, bill.id))

    total_tagihan = sum((bill.total_tagihan for bill in bills), Decimal("0"))
    total_dibayar = sum((bill.total_dibayar for bill in bills), Decimal("0"))
    total_sisa = sum((bill.sisa_tagihan for bill in bills), Decimal("0"))
    jatuh_tempo_list = [bill.jatuh_tempo for bill in bills if bill.jatuh_tempo]
    batas_pembayaran = min(jatuh_tempo_list).strftime("%d %B %Y") if jatuh_tempo_list else "-"

    lines = [
        "Assalamu'alaikum warahmatullahi wabarakatuh.",
        "",
        f"Yth. Bapak/Ibu Wali Santri *{student.nama_lengkap}*,",
        "",
        "*[ Informasi Tanggungan Santri ]*",
        "",
        "Berikut tanggungan yang masih perlu ditunaikan:",
        "",
    ]

    for index, bill in enumerate(bills, start=1):
        periode_label = format_period_label(bill)
        status_text = format_bill_status(bill)
        lines.append(f"{index}. *{bill.jenis_pembayaran.nama} — {periode_label}*")
        lines.append(f"   Sisa: {format_rupiah(bill.sisa_tagihan)} _({status_text})_")
        if bill.jatuh_tempo:
            lines.append(f"   Jatuh Tempo: {bill.jatuh_tempo.strftime('%d %B %Y')}")
        lines.append("")

    lines.extend(
        [
            "_____________________________",
            "",
            "?? *Rekap Tagihan:*",
            f"Total Tagihan : {format_rupiah(total_tagihan)}",
            f"Total Dibayar : {format_rupiah(total_dibayar)}",
            f"*Total Sisa     : {format_rupiah(total_sisa)}*",
            f"? *Batas Pembayaran: {batas_pembayaran}*",
            "_____________________________",
            "",
            "Mohon kiranya Bapak/Ibu berkenan menyelesaikan pembayaran sebelum batas waktu demi kelancaran operasional pesantren.",
            "",
        ]
    )

    if profile.bank_nama or profile.bank_nomor_rekening or profile.bank_atas_nama:
        lines.append("?? *Transfer Bank:*")
        lines.append(f"{profile.bank_nama or '-'} — No. Rek: *{profile.bank_nomor_rekening or '-'}*")
        lines.append(f"a.n. {profile.bank_atas_nama or '-'}")
        lines.append("")

    if profile.qris_url:
        lines.append("?? *Bayar via QRIS:*")
        lines.append(profile.qris_url)
        lines.append("")

    if invoice_url:
        lines.append("?? *Unduh Invoice:*")
        lines.append(invoice_url)
        lines.append("")

    contact_name = profile.bendahara_nama or "Admin"
    contact_number = profile.wa_admin or profile.bendahara_telepon
    if contact_name or contact_number:
        lines.append("?? *Konfirmasi & Pertanyaan:*")
        lines.append(f"{contact_name} — *{contact_number or '-'}*")
        lines.append("")

    lines.append(build_payment_footer(profile))
    return "\n".join(lines)


def build_bill_reminder_message(bill, invoice_url=None):
    return build_reminder_message(bill.santri, [bill], invoice_url=invoice_url)


def build_student_reminder_message(student, bills, invoice_url=None):
    return build_reminder_message(student, bills, invoice_url=invoice_url)


def build_whatsapp_url(number, message):
    normalized = normalize_phone_number(number)
    if not normalized:
        return ""
    return f"https://wa.me/{normalized}?text={quote(message)}"


