import secrets
import string
from datetime import datetime, timezone
from pathlib import Path

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.sale import Receipt, Sale
from app.models.store import Store
from app.services.money import format_xaf

STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "receipts"
ACCENT = colors.HexColor("#8B5A2B")
INK = colors.HexColor("#1A1A1A")
LINE = colors.HexColor("#D9D2C5")


def _verification_key() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(26))


def next_receipt_number(db: Session, year: int | None = None) -> str:
    year = year or datetime.now(timezone.utc).year
    prefix = f"R-{year}-"
    latest = db.scalar(
        select(func.max(Receipt.number)).where(Receipt.number.like(f"{prefix}%"))
    )
    if latest:
        try:
            seq = int(latest.rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def verification_url(number: str, key: str) -> str:
    settings = get_settings()
    return f"{settings.frontend_url.rstrip('/')}/recus/{number}?cle={key}"


def build_receipt_pdf(
    store: Store,
    sale: Sale,
    receipt: Receipt,
    output_path: Path,
) -> Path:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    verify_url = verification_url(receipt.number, receipt.verification_key)
    qr_path = output_path.with_suffix(".qr.png")
    qrcode.make(verify_url).save(qr_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "StoreTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=INK,
        spaceAfter=2,
    )
    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontSize=10,
        textColor=ACCENT,
        spaceBefore=2,
        spaceAfter=0,
    )
    meta_value = ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontSize=11,
        textColor=INK,
        spaceAfter=4,
    )
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, textColor=INK)
    footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=ACCENT,
        alignment=1,
    )

    phone = store.phone or store.whatsapp_number or ""
    if phone and not phone.startswith("+"):
        phone = f"+{phone}"

    sale_date = sale.created_at.astimezone(timezone.utc).strftime("%d/%m/%Y")
    customer = receipt.customer_name or "Sans nom"

    story = []
    header = Table(
        [
            [
                Paragraph(store.name, title),
                Paragraph(
                    f"<b>Recu</b><br/>{receipt.number}",
                    ParagraphStyle("RightHead", parent=body, alignment=2, fontSize=12),
                ),
            ]
        ],
        colWidths=[110 * mm, 60 * mm],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(header)
    if phone:
        story.append(Paragraph(f"Tel. : {phone}", body))
    story.append(Spacer(1, 8 * mm))

    for label, value in [
        ("Date", sale_date),
        ("Code vente", sale.public_code),
        ("Client", customer),
    ]:
        story.append(Paragraph(label, meta_label))
        story.append(Paragraph(value, meta_value))

    story.append(Spacer(1, 6 * mm))

    table_data = [["Article", "Qte", "Prix unit.", "Montant"]]
    for item in sale.items:
        table_data.append(
            [
                item.name,
                str(item.quantity),
                format_xaf(item.unit_price),
                format_xaf(item.total_price),
            ]
        )
    table_data.append(["", "", "Total", format_xaf(sale.total_amount)])

    table = Table(table_data, colWidths=[70 * mm, 20 * mm, 35 * mm, 35 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
                ("LINEBELOW", (0, -2), (-1, -2), 0.6, LINE),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12 * mm))

    qr_img = Image(str(qr_path), width=28 * mm, height=28 * mm)
    verify_block = Table(
        [
            [
                qr_img,
                Paragraph(
                    "Pour verifier ce document, scannez ce code ou ouvrez le lien ci-dessous.<br/><br/>"
                    f'<font color="#8B5A2B">{verify_url}</font>',
                    body,
                ),
            ]
        ],
        colWidths=[34 * mm, 136 * mm],
    )
    verify_block.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(verify_block)
    story.append(Spacer(1, 14 * mm))
    story.append(
        Paragraph("Recu genere avec Komero · komero.app", footer)
    )

    doc.build(story)
    if qr_path.exists():
        qr_path.unlink(missing_ok=True)
    return output_path


def create_receipt(
    db: Session,
    store: Store,
    sale: Sale,
    customer_name: str | None,
) -> Receipt:
    existing = db.scalar(select(Receipt).where(Receipt.sale_id == sale.id))
    sale_full = db.scalar(
        select(Sale).options(joinedload(Sale.items)).where(Sale.id == sale.id)
    )
    assert sale_full is not None

    if existing:
        if customer_name and not existing.customer_name:
            existing.customer_name = customer_name
            sale.customer_name = customer_name
            db.commit()
            db.refresh(existing)
        pdf_path = Path(existing.pdf_path or "")
        if not pdf_path.exists():
            filename = f"Receipt-{existing.number}.pdf"
            pdf_path = STORAGE_DIR / filename
            existing.pdf_path = str(pdf_path)
            db.commit()
            build_receipt_pdf(store, sale_full, existing, pdf_path)
        return existing

    number = next_receipt_number(db)
    key = _verification_key()
    filename = f"Receipt-{number}.pdf"
    pdf_path = STORAGE_DIR / filename

    receipt = Receipt(
        store_id=store.id,
        sale_id=sale.id,
        number=number,
        verification_key=key,
        customer_name=customer_name,
        pdf_path=str(pdf_path),
    )
    db.add(receipt)
    sale.customer_name = customer_name
    db.commit()
    db.refresh(receipt)

    build_receipt_pdf(store, sale_full, receipt, pdf_path)
    return receipt


def get_receipt_by_number(db: Session, number: str) -> Receipt | None:
    return db.scalar(
        select(Receipt)
        .options(
            joinedload(Receipt.sale).joinedload(Sale.items),
            joinedload(Receipt.store),
        )
        .where(Receipt.number == number)
    )
