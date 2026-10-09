import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.order import (
    DeliveryStatus,
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
)
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.services.onboarding import normalize_phone
from app.services.products import get_product


ORDER_CODE_RE = re.compile(r"\bref:([A-Z0-9]{6})\b")
SALE_NOTE_RE = re.compile(
    r"sale:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.I,
)


def _short_ref(order_id: uuid.UUID) -> str:
    return order_id.hex[:6].upper()


def merchant_notify_number(db: Session, store: Store) -> str | None:
    owner = db.get(User, store.owner_id)
    for candidate in (
        owner.phone if owner else None,
        store.phone,
        store.whatsapp_number,
    ):
        if not candidate:
            continue
        digits = normalize_phone(candidate)
        if digits:
            return digits
    return None


def get_or_create_customer(
    db: Session,
    store: Store,
    *,
    phone: str | None,
    name: str | None = None,
) -> Customer | None:
    if not phone:
        return None
    normalized = normalize_phone(phone)
    if not normalized:
        return None
    existing = db.scalar(
        select(Customer).where(
            Customer.store_id == store.id,
            Customer.whatsapp_number.in_(
                [phone, normalized, f"+{normalized}"]
            ),
        )
    )
    if existing:
        if name and not existing.name:
            existing.name = name[:120]
            db.commit()
            db.refresh(existing)
        return existing

    customer = Customer(
        store_id=store.id,
        name=(name or None),
        phone=f"+{normalized}",
        whatsapp_number=normalized,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def create_catalog_order(
    db: Session,
    store: Store,
    *,
    product: Product,
    quantity: int = 1,
    unit_price: Decimal | None = None,
    customer_phone: str | None = None,
    customer_name: str | None = None,
    variant: str | None = None,
    notes: str | None = None,
) -> Order:
    qty = max(1, int(quantity or 1))
    price = Decimal(str(unit_price if unit_price is not None else product.price))
    customer = get_or_create_customer(
        db, store, phone=customer_phone, name=customer_name
    )
    note_parts: list[str] = []
    if variant:
        note_parts.append(f"variant:{variant.strip()[:80]}")
    if notes:
        note_parts.append(notes.strip()[:400])
    if customer_phone:
        note_parts.append(f"customer_wa:{normalize_phone(customer_phone)}")

    order = Order(
        store_id=store.id,
        customer_id=customer.id if customer else None,
        status=OrderStatus.PENDING,
        total_amount=price * qty,
        currency=store.currency or "XAF",
        payment_status=PaymentStatus.UNPAID,
        delivery_status=DeliveryStatus.NOT_STARTED,
        notes=" | ".join(note_parts) if note_parts else None,
        items=[
            OrderItem(
                product_id=product.id,
                quantity=qty,
                unit_price=price,
                total_price=price * qty,
            )
        ],
    )
    db.add(order)
    db.flush()
    prefix = f"ref:{_short_ref(order.id)}"
    order.notes = f"{prefix} | {order.notes}" if order.notes else prefix
    db.commit()
    db.refresh(order)
    return get_order(db, order.id)  # type: ignore[return-value]


def get_order(db: Session, order_id: uuid.UUID) -> Order | None:
    return db.scalar(
        select(Order)
        .options(joinedload(Order.items), joinedload(Order.customer))
        .where(Order.id == order_id)
    )


def get_order_for_store(
    db: Session, store_id: uuid.UUID, order_id: uuid.UUID
) -> Order | None:
    return db.scalar(
        select(Order)
        .options(joinedload(Order.items), joinedload(Order.customer))
        .where(Order.id == order_id, Order.store_id == store_id)
    )


def order_ref(order: Order) -> str:
    match = ORDER_CODE_RE.search(order.notes or "")
    if match:
        return match.group(1)
    return _short_ref(order.id)


def order_sale_id(order: Order) -> uuid.UUID | None:
    match = SALE_NOTE_RE.search(order.notes or "")
    if not match:
        return None
    try:
        return uuid.UUID(match.group(1))
    except ValueError:
        return None


def attach_sale_to_order(db: Session, order: Order, sale_id: uuid.UUID) -> Order:
    notes = order.notes or ""
    if f"sale:{sale_id}" not in notes:
        order.notes = f"{notes} | sale:{sale_id}".strip(" |")
    db.commit()
    db.refresh(order)
    return get_order(db, order.id)  # type: ignore[return-value]


def mark_order_paid(db: Session, order: Order) -> Order:
    order.payment_status = PaymentStatus.PAID
    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CONFIRMED
    db.commit()
    db.refresh(order)
    return get_order(db, order.id)  # type: ignore[return-value]


def cancel_order(db: Session, order: Order) -> Order:
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return get_order(db, order.id)  # type: ignore[return-value]


def order_line_label(db: Session, order: Order) -> str:
    if not order.items:
        return "Article"
    item = order.items[0]
    product = (
        get_product(db, order.store_id, item.product_id)
        if item.product_id
        else None
    )
    name = product.name if product else "Article"
    variant_match = re.search(r"variant:([^|]+)", order.notes or "")
    if variant_match:
        return f"{name} ({variant_match.group(1).strip()})"
    return name


def sale_items_from_order(db: Session, order: Order) -> list[dict]:
    items: list[dict] = []
    for item in order.items:
        product = (
            get_product(db, order.store_id, item.product_id)
            if item.product_id
            else None
        )
        items.append(
            {
                "name": product.name if product else "Article",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "product_id": str(item.product_id) if item.product_id else None,
            }
        )
    return items


def find_recent_catalog_order(
    db: Session,
    store_id: uuid.UUID,
    product_id: uuid.UUID,
    *,
    within_minutes: int = 15,
) -> Order | None:
    since = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
    orders = list(
        db.scalars(
            select(Order)
            .options(joinedload(Order.items), joinedload(Order.customer))
            .where(
                Order.store_id == store_id,
                Order.status == OrderStatus.PENDING,
                Order.payment_status == PaymentStatus.UNPAID,
                Order.created_at >= since,
            )
            .order_by(Order.created_at.desc())
            .limit(12)
        ).unique()
    )
    for order in orders:
        if any(item.product_id == product_id for item in order.items):
            return order
    return None


def attach_customer_to_order(
    db: Session,
    store: Store,
    order: Order,
    *,
    phone: str,
    name: str | None = None,
) -> Order:
    customer = get_or_create_customer(db, store, phone=phone, name=name)
    if customer:
        order.customer_id = customer.id
    notes = order.notes or ""
    marker = f"customer_wa:{normalize_phone(phone)}"
    if marker not in notes:
        order.notes = f"{notes} | {marker}".strip(" |")
    db.commit()
    db.refresh(order)
    return get_order(db, order.id)  # type: ignore[return-value]
