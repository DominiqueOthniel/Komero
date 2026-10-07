import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductStatus


class ProductImageIn(BaseModel):
    image_url: str = Field(max_length=500)
    position: int = 0


class ProductVariantIn(BaseModel):
    name: str = Field(max_length=80)
    value: str = Field(max_length=80)
    stock_quantity: int = 0
    price: Decimal | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(ge=0)
    compare_price: Decimal | None = Field(default=None, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    sku: str | None = None
    category_id: uuid.UUID | None = None
    status: ProductStatus = ProductStatus.DRAFT
    images: list[ProductImageIn] = []
    variants: list[ProductVariantIn] = []


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    compare_price: Decimal | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    sku: str | None = None
    category_id: uuid.UUID | None = None
    status: ProductStatus | None = None
    images: list[ProductImageIn] | None = None
    variants: list[ProductVariantIn] | None = None


class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    position: int


class ProductVariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    value: str
    stock_quantity: int
    price: Decimal | None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    compare_price: Decimal | None
    stock_quantity: int
    sku: str | None
    category_id: uuid.UUID | None
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageOut] = []
    variants: list[ProductVariantOut] = []


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID
    name: str
    slug: str
