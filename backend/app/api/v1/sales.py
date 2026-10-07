import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_owned_store
from app.models.store import Store
from app.models.user import User
from app.schemas.sale import ReceiptCreate, ReceiptOut, SaleCreate, SaleOut
from app.services.receipts import create_receipt, verification_url
from app.services.sales import create_sale, get_sale, list_sales

router = APIRouter(tags=["sales"])


def _sale_out(sale) -> SaleOut:
    receipt = None
    if sale.receipt:
        receipt = ReceiptOut(
            id=sale.receipt.id,
            number=sale.receipt.number,
            customer_name=sale.receipt.customer_name,
            created_at=sale.receipt.created_at,
            verification_url=verification_url(
                sale.receipt.number, sale.receipt.verification_key
            ),
        )
    return SaleOut(
        id=sale.id,
        store_id=sale.store_id,
        public_code=sale.public_code,
        currency=sale.currency,
        total_amount=sale.total_amount,
        item_count=sale.item_count,
        customer_name=sale.customer_name,
        status=sale.status.value if hasattr(sale.status, "value") else str(sale.status),
        created_at=sale.created_at,
        items=sale.items,
        receipt=receipt,
    )


@router.get("/stores/{store_id}/sales", response_model=list[SaleOut])
def get_sales(
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SaleOut]:
    return [_sale_out(sale) for sale in list_sales(db, store.id)]


@router.post("/stores/{store_id}/sales", response_model=SaleOut, status_code=201)
def post_sale(
    payload: SaleCreate,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SaleOut:
    try:
        sale = create_sale(
            db,
            store,
            [item.model_dump() for item in payload.items],
            customer_name=payload.customer_name,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _sale_out(sale)


@router.get("/stores/{store_id}/sales/{sale_id}", response_model=SaleOut)
def get_one_sale(
    sale_id: uuid.UUID,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SaleOut:
    sale = get_sale(db, sale_id)
    if not sale or sale.store_id != store.id:
        raise HTTPException(status_code=404, detail="Sale not found")
    return _sale_out(sale)


@router.post(
    "/stores/{store_id}/sales/{sale_id}/receipt",
    response_model=ReceiptOut,
    status_code=201,
)
def post_receipt(
    sale_id: uuid.UUID,
    payload: ReceiptCreate,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ReceiptOut:
    sale = get_sale(db, sale_id)
    if not sale or sale.store_id != store.id:
        raise HTTPException(status_code=404, detail="Sale not found")
    receipt = create_receipt(db, store, sale, payload.customer_name)
    return ReceiptOut(
        id=receipt.id,
        number=receipt.number,
        customer_name=receipt.customer_name,
        created_at=receipt.created_at,
        verification_url=verification_url(receipt.number, receipt.verification_key),
    )


@router.get("/stores/{store_id}/sales/{sale_id}/receipt.pdf")
def download_receipt_pdf(
    sale_id: uuid.UUID,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    sale = get_sale(db, sale_id)
    if not sale or sale.store_id != store.id or not sale.receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    path = Path(sale.receipt.pdf_path or "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF missing")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"Receipt-{sale.receipt.number}.pdf",
    )
