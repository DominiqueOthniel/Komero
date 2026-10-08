import secrets
import string
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.store import Store


ALPHABET = string.digits + string.ascii_uppercase


def generate_sale_code(db: Session, store_id: uuid.UUID) -> str:
    for _ in range(20):
        code = "C-" + "".join(secrets.choice(ALPHABET) for _ in range(4))
        exists = db.scalar(
            select(Sale.id).where(Sale.store_id == store_id, Sale.public_code == code)
        )
        if not exists:
            return code
    return f"C-{uuid.uuid4().hex[:4].upper()}"


def create_sale(
    db: Session,
    store: Store,
    items: list[dict],
    customer_name: str | None = None,
    notes: str | None = None,
) -> Sale:
    if not items:
        raise ValueError("A sale needs at least one item")

    sale_items: list[SaleItem] = []
    total = Decimal("0")
    item_count = 0

    for raw in items:
        name = str(raw["name"]).strip()
        quantity = int(raw.get("quantity") or 1)
        unit_price = Decimal(str(raw["unit_price"]))
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        line_total = unit_price * quantity
        total += line_total
        item_count += quantity
        product_id = raw.get("product_id")
        sale_items.append(
            SaleItem(
                product_id=uuid.UUID(str(product_id)) if product_id else None,
                name=name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=line_total,
            )
        )

    sale = Sale(
        store_id=store.id,
        public_code=generate_sale_code(db, store.id),
        currency=store.currency or "XAF",
        total_amount=total,
        item_count=item_count,
        customer_name=customer_name,
        notes=notes,
        status=SaleStatus.RECORDED,
        items=sale_items,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return get_sale(db, sale.id)


def get_sale(db: Session, sale_id: uuid.UUID) -> Sale | None:
    return db.scalar(
        select(Sale)
        .options(joinedload(Sale.items), joinedload(Sale.receipt))
        .where(Sale.id == sale_id)
    )


def get_sale_by_code(db: Session, store_id: uuid.UUID, public_code: str) -> Sale | None:
    return db.scalar(
        select(Sale)
        .options(joinedload(Sale.items), joinedload(Sale.receipt))
        .where(
            Sale.store_id == store_id,
            Sale.public_code == public_code.upper(),
        )
    )


def list_sales(db: Session, store_id: uuid.UUID, limit: int = 50) -> list[Sale]:
    return list(
        db.scalars(
            select(Sale)
            .options(joinedload(Sale.items), joinedload(Sale.receipt))
            .where(Sale.store_id == store_id)
            .order_by(Sale.created_at.desc())
            .limit(limit)
        ).unique()
    )


def match_product_by_name(db: Session, store_id: uuid.UUID, name: str) -> Product | None:
    needle = name.strip().lower()
    products = db.scalars(select(Product).where(Product.store_id == store_id)).all()
    for product in products:
        if product.name.lower() == needle:
            return product
    for product in products:
        if needle in product.name.lower() or product.name.lower() in needle:
            return product
    return None


def cancel_sale(db: Session, sale: Sale) -> Sale:
    sale.status = SaleStatus.CANCELLED
    db.commit()
    db.refresh(sale)
    return get_sale(db, sale.id)  # type: ignore[return-value]
