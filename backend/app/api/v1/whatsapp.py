from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.factory import get_ai_provider
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_owned_store
from app.models.conversation import Conversation, Message
from app.models.store import Store
from app.models.user import User
from app.services.conversation_engine import handle_incoming_message
from app.services.whatsapp_webhook import process_webhook_payload
from app.whatsapp.factory import get_whatsapp_adapter
from app.whatsapp.mock import MockWhatsAppAdapter

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        # Meta expects the raw challenge echoed as plain text.
        return PlainTextResponse(content=str(hub_challenge or ""), status_code=200)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    payload = await request.json()
    adapter = get_whatsapp_adapter()
    result = process_webhook_payload(db, adapter, payload)
    return {"status": "received", **result}


class ExtractProductRequest(BaseModel):
    text: str
    language: str = "fr"


class SimulateMessageRequest(BaseModel):
    from_number: str = Field(min_length=8, max_length=40)
    text: str = ""
    button_id: str | None = None
    media_id: str | None = None
    media_kind: str | None = None
    mime_type: str | None = None


@router.post("/ai/extract-product")
def extract_product_preview(
    payload: ExtractProductRequest,
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    provider = get_ai_provider()
    return provider.extract_product(payload.text, language=payload.language)


@router.get("/adapter")
def adapter_status(_: User = Depends(get_current_user)) -> dict[str, str]:
    settings = get_settings()
    adapter = get_whatsapp_adapter()
    return {
        "configured_adapter": settings.whatsapp_adapter,
        "runtime_adapter": adapter.__class__.__name__,
    }


@router.post("/stores/{store_id}/simulate")
def simulate_inbound(
    payload: SimulateMessageRequest,
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Local/dev helper that drives the conversation engine without Meta."""
    adapter = get_whatsapp_adapter()
    if isinstance(adapter, MockWhatsAppAdapter):
        adapter.sent.clear()
    result = handle_incoming_message(
        db,
        adapter,
        store=store,
        from_number=payload.from_number,
        text=payload.text,
        button_id=payload.button_id,
        media_id=payload.media_id,
        media_kind=payload.media_kind,
        mime_type=payload.mime_type,
    )
    outbound = []
    if isinstance(adapter, MockWhatsAppAdapter):
        outbound = list(adapter.sent)
    return {"result": result, "outbound": outbound}


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    direction: str
    message_type: str
    content: str | None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    whatsapp_number: str
    status: str
    state: str
    updated_at: datetime
    messages: list[MessageOut] = []


@router.get("/stores/{store_id}/conversations", response_model=list[ConversationOut])
def list_conversations(
    store: Store = Depends(get_owned_store),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.store_id == store.id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
    )
