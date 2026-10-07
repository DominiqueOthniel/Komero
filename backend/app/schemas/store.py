import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.store import StoreStatus


class StoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    phone: str | None = None
    whatsapp_number: str | None = None
    currency: str = "XAF"
    primary_color: str = "#0F6B5C"


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    phone: str | None = None
    whatsapp_number: str | None = None
    logo_url: str | None = None
    currency: str | None = None
    primary_color: str | None = None
    status: StoreStatus | None = None


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    currency: str
    phone: str | None
    whatsapp_number: str | None
    primary_color: str
    status: StoreStatus
    created_at: datetime
    updated_at: datetime
