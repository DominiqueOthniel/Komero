import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StoreStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    currency: Mapped[str] = mapped_column(String(8), default="XAF", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    whatsapp_number: Mapped[str | None] = mapped_column(String(40), index=True)
    primary_color: Mapped[str] = mapped_column(String(20), default="#0F6B5C")
    status: Mapped[StoreStatus] = mapped_column(
        Enum(StoreStatus, name="store_status"), default=StoreStatus.DRAFT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner = relationship("User", back_populates="stores")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    categories = relationship(
        "Category", back_populates="store", cascade="all, delete-orphan"
    )
    customers = relationship(
        "Customer", back_populates="store", cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="store", cascade="all, delete-orphan")
    receipts = relationship(
        "Receipt", back_populates="store", cascade="all, delete-orphan"
    )
    whatsapp_connection = relationship(
        "WhatsAppConnection",
        back_populates="store",
        uselist=False,
        cascade="all, delete-orphan",
    )
