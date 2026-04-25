from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from accounts.models import PondokProfile


def build_bill_invoice_pdf(bill):
    profile = PondokProfile.get_solo()
    logo_path = Path(settings.BASE_DIR) / "static" / "img" / "pondok-logo.png"
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="InvoiceTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#6B4F3A"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="InvoiceMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6B7280"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionLabel",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#3E2C23"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )

    invoice_number = f"INV-{bill.santri.nis}-{bill.periode_bulan:02d}{bill.periode_tahun}"
    issue_date = timezone.localdate().strftime("%d-%m-%Y")
    due_date = bill.jatuh_tempo.strftime("%d-%m-%Y") if bill.jatuh_tempo else "-"

    story = [
        Image(str(logo_path), width=24 * mm, height=24 * mm) if logo_path.exists() else Spacer(1, 2 * mm),
        Spacer(1, 4 * mm),
        Paragraph(profile.display_name or "Pondok Pesantren", styles["InvoiceMeta"]),
        Paragraph("INVOICE TAGIHAN SANTRI", styles["InvoiceMeta"]),
        Paragraph(f"Invoice #{invoice_number}", styles["InvoiceTitle"]),
        Paragraph(
            profile.display_address or "Identitas pondok belum dilengkapi.",
            styles["InvoiceMeta"],
        ),
        Paragraph(
            " | ".join(part for part in [profile.telepon, profile.wa_admin, profile.email] if part) or " ",
            styles["InvoiceMeta"],
        ),
        Paragraph(
            "Dokumen ringkas tagihan yang bisa dibagikan melalui WhatsApp atau diunduh sebagai arsip.",
            styles["InvoiceMeta"],
        ),
        Spacer(1, 8),
    ]

    summary_rows = [
        ["Santri", bill.santri.nama_lengkap],
        ["NIS", bill.santri.nis],
        ["Jenis Pembayaran", bill.jenis_pembayaran.nama],
        ["Periode", f"{bill.periode_bulan}/{bill.periode_tahun}"],
        ["Tanggal Terbit", issue_date],
        ["Jatuh Tempo", due_date],
        ["Status", bill.effective_status_label],
    ]
    summary_table = Table(summary_rows, colWidths=[38 * mm, 120 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F6EFE6")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#3E2C23")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8C7B7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#FCFAF7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 10)])

    story.append(Paragraph("Rincian Nominal", styles["SectionLabel"]))
    amount_rows = [
        ["Nominal", f"Rp {bill.nominal:,.0f}".replace(",", ".")],
        ["Diskon", f"Rp {bill.diskon:,.0f}".replace(",", ".")],
        ["Denda", f"Rp {bill.denda:,.0f}".replace(",", ".")],
        ["Total Tagihan", f"Rp {bill.total_tagihan:,.0f}".replace(",", ".")],
        ["Sudah Dibayar", f"Rp {bill.total_dibayar:,.0f}".replace(",", ".")],
        ["Sisa Tagihan", f"Rp {bill.sisa_tagihan:,.0f}".replace(",", ".")],
    ]
    amount_table = Table(amount_rows, colWidths=[50 * mm, 108 * mm])
    amount_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F6EFE6")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8C7B7")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#FCFAF7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([amount_table, Spacer(1, 10)])

    story.append(Paragraph("Riwayat Pembayaran", styles["SectionLabel"]))
    payments = list(bill.payments.select_related("diterima_oleh").order_by("-tanggal_bayar", "-id"))
    if payments:
        payment_rows = [["Tanggal", "Nomor", "Jumlah", "Metode", "Verifikasi"]]
        for payment in payments:
            payment_rows.append(
                [
                    payment.tanggal_bayar.strftime("%d-%m-%Y"),
                    payment.nomor_transaksi,
                    f"Rp {payment.jumlah_bayar:,.0f}".replace(",", "."),
                    payment.get_metode_bayar_display(),
                    "Ya" if payment.verified else "Belum",
                ]
            )
        payment_table = Table(payment_rows, colWidths=[28 * mm, 54 * mm, 34 * mm, 26 * mm, 20 * mm])
        payment_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6B4F3A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8C7B7")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF7F2")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(payment_table)
    else:
        story.append(Paragraph("Belum ada pembayaran yang tercatat untuk tagihan ini.", styles["InvoiceMeta"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
