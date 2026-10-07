from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sale import PublicReceiptOut, SaleItemOut
from app.services.receipts import get_receipt_by_number, verification_url

router = APIRouter(prefix="/public/receipts", tags=["public-receipts"])


@router.get("/{number}", response_model=PublicReceiptOut)
def get_public_receipt(
    number: str,
    cle: str = Query(..., min_length=8),
    db: Session = Depends(get_db),
) -> PublicReceiptOut:
    receipt = get_receipt_by_number(db, number)
    if not receipt or receipt.verification_key != cle:
        raise HTTPException(status_code=404, detail="Receipt not found")
    sale = receipt.sale
    store = receipt.store
    phone = store.phone or store.whatsapp_number
    return PublicReceiptOut(
        number=receipt.number,
        store_name=store.name,
        store_phone=phone,
        sale_code=sale.public_code,
        customer_name=receipt.customer_name,
        currency=sale.currency,
        total_amount=sale.total_amount,
        created_at=receipt.created_at,
        sale_date=sale.created_at,
        items=[SaleItemOut.model_validate(item) for item in sale.items],
        verification_url=verification_url(receipt.number, receipt.verification_key),
    )


@router.get("/{number}/pdf")
def get_public_receipt_pdf(
    number: str,
    cle: str = Query(..., min_length=8),
    db: Session = Depends(get_db),
) -> FileResponse:
    receipt = get_receipt_by_number(db, number)
    if not receipt or receipt.verification_key != cle:
        raise HTTPException(status_code=404, detail="Receipt not found")
    path = Path(receipt.pdf_path or "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF missing")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"Receipt-{receipt.number}.pdf",
    )
