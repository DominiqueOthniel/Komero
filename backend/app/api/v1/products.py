import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_owned_store
from app.models.product import Category, Product
from app.models.store import Store
from app.schemas.product import (
    CategoryCreate,
    CategoryOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.services import products as product_service

router = APIRouter(tags=["products"])


@router.get("/stores/{store_id}/products", response_model=list[ProductOut])
def list_products(
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> list[Product]:
    return product_service.list_products(db, store.id)


@router.post(
    "/stores/{store_id}/products",
    response_model=ProductOut,
    status_code=201,
)
def create_product(
    payload: ProductCreate,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> Product:
    return product_service.create_product(db, store.id, payload)


@router.get("/stores/{store_id}/products/{product_id}", response_model=ProductOut)
def get_product(
    product_id: uuid.UUID,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> Product:
    product = product_service.get_product(db, store.id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/stores/{store_id}/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> Product:
    product = product_service.get_product(db, store.id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_service.update_product(db, product, payload)


@router.delete("/stores/{store_id}/products/{product_id}", status_code=204)
def delete_product(
    product_id: uuid.UUID,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> None:
    product = product_service.get_product(db, store.id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_service.delete_product(db, product)


@router.get("/stores/{store_id}/categories", response_model=list[CategoryOut])
def list_categories(
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> list[Category]:
    return list(
        db.scalars(select(Category).where(Category.store_id == store.id).order_by(Category.name))
    )


@router.post(
    "/stores/{store_id}/categories",
    response_model=CategoryOut,
    status_code=201,
)
def create_category(
    payload: CategoryCreate,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> Category:
    return product_service.create_category(db, store.id, payload)
