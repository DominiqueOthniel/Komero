import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.store import Store, StoreStatus
from app.models.user import User, UserRole
from app.services.slug import slugify


def normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or value.strip()


def find_store_by_merchant_phone(db: Session, phone: str) -> Store | None:
    normalized = normalize_phone(phone)
    candidates = {phone, normalized, f"+{normalized}"}
    if normalized.startswith("237") and len(normalized) > 3:
        candidates.add(normalized[3:])
        candidates.add(f"+{normalized}")
    return db.scalar(select(Store).where(Store.whatsapp_number.in_(list(candidates))))


def find_or_create_merchant_store(db: Session, phone: str) -> Store:
    existing = find_store_by_merchant_phone(db, phone)
    if existing:
        return existing

    normalized = normalize_phone(phone)
    display = f"+{normalized}" if not phone.startswith("+") else phone
    email = f"wa.{normalized}@komero.cm"
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            name=f"Merchant {normalized[-4:]}",
            email=email,
            phone=display,
            password_hash=hash_password(secrets.token_urlsafe(16)),
            role=UserRole.MERCHANT,
        )
        db.add(user)
        db.flush()

    base = slugify(f"boutique-{normalized[-6:]}")
    slug = base
    index = 2
    while db.scalar(select(Store.id).where(Store.slug == slug)):
        slug = f"{base}-{index}"
        index += 1

    store = Store(
        owner_id=user.id,
        name="Nouvelle boutique",
        slug=slug,
        phone=display,
        whatsapp_number=display,
        currency="XAF",
        status=StoreStatus.DRAFT,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def activate_store_with_name(db: Session, store: Store, name: str) -> Store:
    clean = " ".join(name.strip().split())
    if not clean:
        raise ValueError("Store name required")
    store.name = clean[:120]
    store.slug = _unique_slug(db, clean, store.id)
    store.status = StoreStatus.ACTIVE
    db.commit()
    db.refresh(store)
    return store


def _unique_slug(db: Session, name: str, store_id: uuid.UUID) -> str:
    base = slugify(name)
    candidate = base
    index = 2
    while True:
        other = db.scalar(select(Store.id).where(Store.slug == candidate))
        if other is None or other == store_id:
            return candidate
        candidate = f"{base}-{index}"
        index += 1
