from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.product import Category, Product, ProductStatus
from app.models.store import Store, StoreStatus
from app.schemas.product import CategoryOut, ProductOut
from app.schemas.store import StoreOut

router = APIRouter(prefix="/public", tags=["public"])

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


@router.get("/media/{kind}/{filename}")
def get_public_media(kind: str, filename: str) -> FileResponse:
    if kind not in ALLOWED_MEDIA_KINDS:
        raise HTTPException(status_code=404, detail="Media not found")
    safe_name = Path(filename).name
    path = (MEDIA_ROOT / kind / safe_name).resolve()
    root = (MEDIA_ROOT / kind).resolve()
    if not str(path).startswith(str(root)) or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(path)
