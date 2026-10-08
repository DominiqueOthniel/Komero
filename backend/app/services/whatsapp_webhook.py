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
                message_type = message.get("type")
                if message_type == "text":
                    text = (message.get("text") or {}).get("body") or ""
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
            # First contact: create a draft merchant shop for onboarding.
            store = find_or_create_merchant_store(db, str(inbound["from"]))

        result = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=str(inbound["from"]),
            text=str(inbound.get("text") or ""),
            button_id=inbound.get("button_id"),
            whatsapp_message_id=inbound.get("id"),
        )
        results.append(result)
    return {"processed": len(results), "results": results}
