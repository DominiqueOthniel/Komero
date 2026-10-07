import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_owned_store
from app.models.store import Store
from app.models.user import User
from app.schemas.store import StoreCreate, StoreOut, StoreUpdate
from app.services import stores as store_service

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=list[StoreOut])
def list_my_stores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Store]:
    return list(
        db.scalars(
            select(Store)
            .where(Store.owner_id == current_user.id)
            .order_by(Store.created_at.desc())
        )
    )


@router.post("", response_model=StoreOut, status_code=201)
def create_store(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Store:
    return store_service.create_store(db, current_user.id, payload)


@router.get("/{store_id}", response_model=StoreOut)
def get_store(store: Store = Depends(get_owned_store)) -> Store:
    return store


@router.patch("/{store_id}", response_model=StoreOut)
def patch_store(
    payload: StoreUpdate,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> Store:
    return store_service.update_store(db, store, payload)


@router.delete("/{store_id}", status_code=204)
def delete_store(
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> None:
    db.delete(store)
    db.commit()
