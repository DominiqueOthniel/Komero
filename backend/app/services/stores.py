import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.store import Store, StoreStatus
from app.schemas.store import StoreCreate, StoreUpdate
from app.services.slug import slugify


def unique_store_slug(db: Session, name: str) -> str:
    base = slugify(name)
    candidate = base
    index = 2
    while db.scalar(select(Store.id).where(Store.slug == candidate)):
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def create_store(db: Session, owner_id: uuid.UUID, payload: StoreCreate) -> Store:
    store = Store(
        owner_id=owner_id,
        name=payload.name,
        slug=unique_store_slug(db, payload.name),
        description=payload.description,
        phone=payload.phone,
        whatsapp_number=payload.whatsapp_number,
        currency=payload.currency,
        primary_color=payload.primary_color,
        status=StoreStatus.ACTIVE,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def update_store(db: Session, store: Store, payload: StoreUpdate) -> Store:
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] and data["name"] != store.name:
        store.slug = unique_store_slug(db, data["name"])
    for key, value in data.items():
        setattr(store, key, value)
    db.commit()
    db.refresh(store)
    return store
