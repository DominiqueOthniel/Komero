import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIActionType(str, enum.Enum):
    EXTRACT_PRODUCT = "extract_product"
    UPDATE_PRODUCT = "update_product"
    INTENT = "intent"
    OTHER = "other"


class AIActionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AIAction(Base):
    __tablename__ = "ai_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
    )
    action_type: Mapped[AIActionType] = mapped_column(
        Enum(AIActionType, name="ai_action_type"), nullable=False
    )
    input: Mapped[str | None] = mapped_column(Text)
    output: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AIActionStatus] = mapped_column(
        Enum(AIActionStatus, name="ai_action_status"),
        default=AIActionStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation = relationship("Conversation", back_populates="ai_actions")
