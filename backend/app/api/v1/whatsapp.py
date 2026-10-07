from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.ai.factory import get_ai_provider
from app.core.config import get_settings
from app.core.deps import get_current_user
from app.models.user import User
from app.whatsapp.factory import get_whatsapp_adapter

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Any:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge or 0)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    """Receive Meta WhatsApp webhooks.

    Phase 2 will route payloads into the conversation engine.
    For now we acknowledge and log structure only.
    """
    _payload = await request.json()
    return {"status": "received"}


class ExtractProductRequest(BaseModel):
    text: str
    language: str = "fr"


@router.post("/ai/extract-product")
def extract_product_preview(
    payload: ExtractProductRequest,
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Dev helper to preview AI product extraction without WhatsApp."""
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
