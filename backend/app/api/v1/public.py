from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.product import Category, Product, ProductStatus
from app.models.store import Store, StoreStatus
from app.schemas.product import CategoryOut, ProductOut
from app.schemas.store import StoreOut
from app.services.conversation_engine import notify_merchant_catalog_order
from app.services.media_store import load_media
from app.services.orders import create_catalog_order, order_ref
from app.services.products import get_product
from app.whatsapp.factory import get_whatsapp_adapter

router = APIRouter(prefix="/public", tags=["public"])


class PublicOrderCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=999)
    variant: str | None = Field(default=None, max_length=80)
    unit_price: Decimal | None = None
    customer_phone: str | None = Field(default=None, max_length=40)

MEDIA_ROOT = Path(__file__).resolve().parents[3] / "storage"
ALLOWED_MEDIA_KINDS = {"products", "inbound", "receipts"}


@router.get("/shops/{slug}", response_model=StoreOut)
def get_public_shop(slug: str, db: Session = Depends(get_db)) -> Store:
    store = db.scalar(
        select(Store).where(Store.slug == slug, Store.status == StoreStatus.ACTIVE)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Shop not found")
    return store


@router.get("/shops/{slug}/products", response_model=list[ProductOut])
def get_public_products(slug: str, db: Session = Depends(get_db)) -> list[Product]:
    store = db.scalar(
        select(Store).where(Store.slug == slug, Store.status == StoreStatus.ACTIVE)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Shop not found")

    return list(
        db.scalars(
            select(Product)
            .where(
                Product.store_id == store.id,
                Product.status == ProductStatus.PUBLISHED,
            )
            .options(
                selectinload(Product.images),
                selectinload(Product.variants),
            )
            .order_by(Product.created_at.desc())
        )
    )


@router.get("/shops/{slug}/products/{product_id}", response_model=ProductOut)
def get_public_product(
    slug: str, product_id: str, db: Session = Depends(get_db)
) -> Product:
    store = db.scalar(
        select(Store).where(Store.slug == slug, Store.status == StoreStatus.ACTIVE)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Shop not found")

    product = db.scalar(
        select(Product)
        .where(
            Product.id == product_id,
            Product.store_id == store.id,
            Product.status == ProductStatus.PUBLISHED,
        )
        .options(
            selectinload(Product.images),
            selectinload(Product.variants),
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/shops/{slug}/categories", response_model=list[CategoryOut])
def get_public_categories(slug: str, db: Session = Depends(get_db)) -> list[Category]:
    store = db.scalar(
        select(Store).where(Store.slug == slug, Store.status == StoreStatus.ACTIVE)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Shop not found")
    return list(
        db.scalars(select(Category).where(Category.store_id == store.id).order_by(Category.name))
    )


@router.post("/shops/{slug}/orders")
def create_public_shop_order(
    slug: str,
    payload: PublicOrderCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    store = db.scalar(
        select(Store).where(Store.slug == slug, Store.status == StoreStatus.ACTIVE)
    )
    if not store:
        raise HTTPException(status_code=404, detail="Shop not found")

    product = get_product(db, store.id, payload.product_id)
    if not product or product.status != ProductStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Product not found")

    order = create_catalog_order(
        db,
        store,
        product=product,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        customer_phone=payload.customer_phone,
        variant=payload.variant,
        notes="source:catalog_web",
    )
    adapter = get_whatsapp_adapter()
    merchant_to = notify_merchant_catalog_order(
        db,
        adapter,
        store,
        order,
        customer_label=payload.customer_phone or "Catalogue web",
    )
    return {
        "order_id": str(order.id),
        "order_ref": order_ref(order),
        "payment_status": order.payment_status.value,
        "total_amount": str(order.total_amount),
        "merchant_notified": bool(merchant_to),
    }


@router.get("/media/{kind}/{filename}", response_model=None)
def get_public_media(
    kind: str, filename: str, db: Session = Depends(get_db)
):
    if kind not in ALLOWED_MEDIA_KINDS:
        raise HTTPException(status_code=404, detail="Media not found")
    safe_name = Path(filename).name
    path = (MEDIA_ROOT / kind / safe_name).resolve()
    root = (MEDIA_ROOT / kind).resolve()
    if str(path).startswith(str(root)) and path.exists() and path.is_file():
        return FileResponse(path)

    loaded = load_media(db, kind=kind, filename=safe_name)
    if not loaded:
        raise HTTPException(status_code=404, detail="Media not found")
    data, content_type = loaded
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
