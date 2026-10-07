import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WhatsAppConnectionStatus(str, enum.Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WhatsAppConnection(Base):
    __tablename__ = "whatsapp_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(String(40), nullable=False)
    phone_number_id: Mapped[str | None] = mapped_column(String(80))
    business_account_id: Mapped[str | None] = mapped_column(String(80))
    access_token: Mapped[str | None] = mapped_column(Text)
    status: Mapped[WhatsAppConnectionStatus] = mapped_column(
        Enum(WhatsAppConnectionStatus, name="whatsapp_connection_status"),
        default=WhatsAppConnectionStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    store = relationship("Store", back_populates="whatsapp_connection")
