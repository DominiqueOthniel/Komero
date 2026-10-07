from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_owned_store
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.store import Store

router = APIRouter(tags=["dashboard"])


class DashboardStats(BaseModel):
    total_sales: Decimal
    orders_count: int
    products_count: int
    customers_count: int
    pending_orders: int


@router.get("/stores/{store_id}/dashboard", response_model=DashboardStats)
def dashboard_stats(
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
) -> DashboardStats:
    sales = db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.store_id == store.id,
            Order.status != OrderStatus.CANCELLED,
        )
    )
    orders_count = db.scalar(
        select(func.count()).select_from(Order).where(Order.store_id == store.id)
    )
    products_count = db.scalar(
        select(func.count()).select_from(Product).where(Product.store_id == store.id)
    )
    customers_count = db.scalar(
        select(func.count()).select_from(Customer).where(Customer.store_id == store.id)
    )
    pending_orders = db.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.store_id == store.id, Order.status == OrderStatus.PENDING)
    )

    return DashboardStats(
        total_sales=Decimal(str(sales or 0)),
        orders_count=int(orders_count or 0),
        products_count=int(products_count or 0),
        customers_count=int(customers_count or 0),
        pending_orders=int(pending_orders or 0),
    )
