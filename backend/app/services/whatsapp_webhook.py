from typing import Any

from sqlalchemy.orm import Session

from app.services.conversation_engine import handle_incoming_message, identify_store
from app.services.onboarding import find_or_create_merchant_store
from app.whatsapp.base import WhatsAppAdapter


def extract_inbound_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id")
            display_phone = metadata.get("display_phone_number")
            for message in value.get("messages") or []:
                text = ""
                button_id = None
                media_id = None
                media_kind = None
                mime_type = None
                message_type = message.get("type")
                if message_type == "text":
                    text = (message.get("text") or {}).get("body") or ""
                elif message_type == "image":
                    image = message.get("image") or {}
                    media_id = image.get("id")
                    media_kind = "image"
                    mime_type = image.get("mime_type") or "image/jpeg"
                    text = image.get("caption") or ""
                elif message_type == "audio":
                    audio = message.get("audio") or {}
                    media_id = audio.get("id")
                    media_kind = "audio"
                    mime_type = audio.get("mime_type") or "audio/ogg"
                elif message_type == "voice":
                    voice = message.get("voice") or {}
                    media_id = voice.get("id")
                    media_kind = "audio"
                    mime_type = voice.get("mime_type") or "audio/ogg"
                elif message_type == "interactive":
                    interactive = message.get("interactive") or {}
                    if interactive.get("type") == "button_reply":
                        reply = interactive.get("button_reply") or {}
                        button_id = reply.get("id")
                        text = reply.get("title") or ""
                    elif interactive.get("type") == "list_reply":
                        reply = interactive.get("list_reply") or {}
                        button_id = reply.get("id")
                        text = reply.get("title") or ""
                elif message_type == "button":
                    button = message.get("button") or {}
                    button_id = button.get("payload") or button.get("text")
                    text = button.get("text") or ""

                messages.append(
                    {
                        "from": message.get("from"),
                        "id": message.get("id"),
                        "text": text,
                        "button_id": button_id,
                        "media_id": media_id,
                        "media_kind": media_kind,
                        "mime_type": mime_type,
                        "phone_number_id": phone_number_id,
                        "display_phone_number": display_phone,
                    }
                )
    return messages


def process_webhook_payload(
    db: Session,
    adapter: WhatsAppAdapter,
    payload: dict[str, Any],
) -> dict[str, Any]:
    results = []
    for inbound in extract_inbound_messages(payload):
        if not inbound.get("from"):
            results.append({"ok": False, "error": "missing_from"})
            continue

        store = identify_store(
            db,
            inbound.get("phone_number_id"),
            inbound.get("display_phone_number"),
            from_number=str(inbound["from"]),
        )
        if not store:
            store = find_or_create_merchant_store(db, str(inbound["from"]))

        result = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=str(inbound["from"]),
            text=str(inbound.get("text") or ""),
            button_id=inbound.get("button_id"),
            whatsapp_message_id=inbound.get("id"),
            media_id=inbound.get("media_id"),
            media_kind=inbound.get("media_kind"),
            mime_type=inbound.get("mime_type"),
        )
        results.append(result)
    return {"processed": len(results), "results": results}
