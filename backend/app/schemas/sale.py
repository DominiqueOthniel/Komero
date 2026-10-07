import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SaleItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(gt=0)
    product_id: uuid.UUID | None = None


class SaleCreate(BaseModel):
    items: list[SaleItemIn] = Field(min_length=1)
    customer_name: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class SaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    product_id: uuid.UUID | None


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: str
    customer_name: str | None
    created_at: datetime
    verification_url: str | None = None


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    public_code: str
    currency: str
    total_amount: Decimal
    item_count: int
    customer_name: str | None
    status: str
    created_at: datetime
    items: list[SaleItemOut]
    receipt: ReceiptOut | None = None


class ReceiptCreate(BaseModel):
    customer_name: str | None = Field(default=None, max_length=120)


class PublicReceiptOut(BaseModel):
    number: str
    store_name: str
    store_phone: str | None
    sale_code: str
    customer_name: str | None
    currency: str
    total_amount: Decimal
    created_at: datetime
    sale_date: datetime
    items: list[SaleItemOut]
    verification_url: str
