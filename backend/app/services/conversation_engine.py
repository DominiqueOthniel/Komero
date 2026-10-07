import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import (
    Conversation,
    ConversationState,
    ConversationStatus,
    Message,
    MessageDirection,
    MessageType,
)
from app.models.store import Store
from app.models.whatsapp import WhatsAppConnection
from app.services.money import format_xaf
from app.services.receipts import create_receipt, verification_url
from app.services.sales import (
    create_sale,
    get_sale,
    get_sale_by_code,
    match_product_by_name,
)
from app.whatsapp.base import WhatsAppAdapter

SALE_PATTERNS = [
    re.compile(
        r"^(?:vente|vendre|sale|sell)\s+(.+?)\s+(?:x\s*)?(\d+)\s+(?:a|à|@)?\s*(\d+(?:[.,]\d+)?)\s*(?:f|fcfa|xaf)?$",
        re.I,
    ),
    re.compile(
        r"^(?:vente|vendre|sale|sell)\s+(.+?)\s+(?:a|à|@)?\s*(\d+(?:[.,]\d+)?)\s*(?:f|fcfa|xaf)?$",
        re.I,
    ),
    re.compile(
        r"^(.+?)\s+(?:x\s*)?(\d+)\s+(?:a|à|@)?\s*(\d+(?:[.,]\d+)?)\s*(?:f|fcfa|xaf)?$",
        re.I,
    ),
    re.compile(
        r"^(.+?)\s+(?:a|à|@)?\s*(\d+(?:[.,]\d+)?)\s*(?:f|fcfa|xaf)$",
        re.I,
    ),
]


def _normalize_button(value: str) -> str:
    return value.strip().lower()


def _parse_sale_text(text: str) -> dict[str, Any] | None:
    cleaned = " ".join(text.strip().split())
    for pattern in SALE_PATTERNS:
        match = pattern.match(cleaned)
        if not match:
            continue
        groups = match.groups()
        try:
            if len(groups) == 3:
                name, qty_raw, price_raw = groups
                quantity = int(qty_raw)
                unit_price = Decimal(price_raw.replace(",", "."))
            else:
                name, price_raw = groups
                quantity = 1
                unit_price = Decimal(price_raw.replace(",", "."))
        except (InvalidOperation, ValueError):
            continue
        name = name.strip(" -:")
        if not name or unit_price <= 0:
            continue
        return {"name": name, "quantity": quantity, "unit_price": unit_price}
    return None


def _get_or_create_conversation(
    db: Session, store: Store, whatsapp_number: str
) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.store_id == store.id,
            Conversation.whatsapp_number == whatsapp_number,
            Conversation.status == ConversationStatus.OPEN,
        )
    )
    if conversation:
        return conversation
    conversation = Conversation(
        store_id=store.id,
        whatsapp_number=whatsapp_number,
        status=ConversationStatus.OPEN,
        state=ConversationState.GENERAL_ASSISTANCE,
        context={},
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def _store_message(
    db: Session,
    conversation: Conversation,
    direction: MessageDirection,
    content: str,
    message_type: MessageType = MessageType.TEXT,
    whatsapp_message_id: str | None = None,
    media_url: str | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        direction=direction,
        message_type=message_type,
        content=content,
        media_url=media_url,
        whatsapp_message_id=whatsapp_message_id,
    )
    db.add(message)
    db.commit()
    return message


def _send_text(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
    body: str,
) -> None:
    result = adapter.send_text(to, body)
    _store_message(
        db,
        conversation,
        MessageDirection.OUTBOUND,
        body,
        MessageType.TEXT,
        whatsapp_message_id=str(result.get("id") or ""),
    )


def _send_buttons(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
    body: str,
    buttons: list[dict[str, str]],
) -> None:
    result = adapter.send_buttons(to, body, buttons)
    _store_message(
        db,
        conversation,
        MessageDirection.OUTBOUND,
        body,
        MessageType.BUTTON,
        whatsapp_message_id=str(result.get("id") or ""),
    )


def identify_store(db: Session, phone_number_id: str | None, to_number: str | None) -> Store | None:
    if phone_number_id:
        connection = db.scalar(
            select(WhatsAppConnection).where(
                WhatsAppConnection.phone_number_id == phone_number_id
            )
        )
        if connection:
            return db.get(Store, connection.store_id)

    if to_number:
        normalized = to_number.lstrip("+")
        store = db.scalar(
            select(Store).where(Store.whatsapp_number.in_([to_number, normalized, f"+{normalized}"]))
        )
        if store:
            return store
    return None


def _sale_recorded_reply(sale) -> tuple[str, list[dict[str, str]]]:
    body = f"Sale recorded: {sale.public_code}."
    buttons = [
        {"id": f"receipt:{sale.public_code}", "title": f"Receipt {sale.public_code}"[:20]},
        {"id": "add_product", "title": "Add a product"},
        {"id": "more_actions", "title": "More actions"},
    ]
    return body, buttons


def _ask_receipt_name(sale) -> tuple[str, list[dict[str, str]]]:
    item_label = "1 item" if sale.item_count == 1 else f"{sale.item_count} items"
    body = (
        f"Receipt for sale {sale.public_code}: {item_label}, {format_xaf(sale.total_amount)}. "
        "In whose name? Write the customer's name, or tap 'No name'."
    )
    buttons = [
        {"id": f"receipt_noname:{sale.public_code}", "title": "No name"},
        {"id": "receipt_cancel", "title": "Cancel"},
    ]
    return body, buttons


def _issue_receipt(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    to: str,
    sale,
    customer_name: str | None,
) -> None:
    receipt = create_receipt(db, store, sale, customer_name)
    filename = f"Receipt-{receipt.number}.pdf"
    caption = f"Here is receipt {receipt.number}. Forward it to your customer."
    result = adapter.send_document(
        to,
        document_path=receipt.pdf_path or "",
        filename=filename,
        caption=caption,
    )
    _store_message(
        db,
        conversation,
        MessageDirection.OUTBOUND,
        caption,
        MessageType.SYSTEM,
        whatsapp_message_id=str(result.get("id") or ""),
        media_url=verification_url(receipt.number, receipt.verification_key),
    )
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    conversation.context = {}
    db.commit()


def handle_incoming_message(
    db: Session,
    adapter: WhatsAppAdapter,
    *,
    store: Store,
    from_number: str,
    text: str,
    button_id: str | None = None,
    whatsapp_message_id: str | None = None,
) -> dict[str, Any]:
    conversation = _get_or_create_conversation(db, store, from_number)
    inbound = text or button_id or ""
    _store_message(
        db,
        conversation,
        MessageDirection.INBOUND,
        inbound,
        MessageType.BUTTON if button_id else MessageType.TEXT,
        whatsapp_message_id=whatsapp_message_id,
    )

    button = _normalize_button(button_id or "")
    content = text.strip()
    lowered = content.lower()

    if conversation.state == ConversationState.WAITING_RECEIPT_NAME:
        sale_id = (conversation.context or {}).get("pending_sale_id")
        sale = get_sale(db, uuid.UUID(sale_id)) if sale_id else None
        if button == "receipt_cancel" or lowered in {"cancel", "annuler"}:
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            conversation.context = {}
            db.commit()
            _send_text(db, adapter, conversation, from_number, "Receipt cancelled.")
            return {"ok": True, "action": "receipt_cancelled"}

        if sale and (
            button.startswith("receipt_noname:")
            or lowered in {"no name", "sans nom", "noname"}
        ):
            _issue_receipt(db, adapter, store, conversation, from_number, sale, None)
            return {"ok": True, "action": "receipt_sent", "receipt": True}

        if sale and content:
            _issue_receipt(db, adapter, store, conversation, from_number, sale, content)
            return {"ok": True, "action": "receipt_sent", "receipt": True}

        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Write the customer name, or tap No name.",
        )
        return {"ok": True, "action": "awaiting_receipt_name"}

    if button.startswith("receipt:") or lowered.startswith("receipt "):
        code = button.split(":", 1)[1] if ":" in button else content.split(" ", 1)[-1]
        sale = get_sale_by_code(db, store.id, code.strip())
        if not sale:
            _send_text(db, adapter, conversation, from_number, "Sale not found.")
            return {"ok": False, "action": "sale_not_found"}
        conversation.state = ConversationState.WAITING_RECEIPT_NAME
        conversation.context = {"pending_sale_id": str(sale.id)}
        db.commit()
        body, buttons = _ask_receipt_name(sale)
        _send_buttons(db, adapter, conversation, from_number, body, buttons)
        return {"ok": True, "action": "ask_receipt_name", "sale_code": sale.public_code}

    if button == "add_product" or lowered in {"add a product", "ajouter produit", "add product"}:
        conversation.state = ConversationState.ADDING_PRODUCT
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Send the product as text, for example: Robe rouge 12000, 5 pieces.",
        )
        return {"ok": True, "action": "add_product_prompt"}

    if button == "more_actions" or lowered in {"more actions", "plus d'actions"}:
        _send_buttons(
            db,
            adapter,
            conversation,
            from_number,
            "What do you want to do?",
            [
                {"id": "record_sale_help", "title": "Record a sale"},
                {"id": "add_product", "title": "Add a product"},
                {"id": "list_products", "title": "My products"},
            ],
        )
        return {"ok": True, "action": "more_actions"}

    if button == "record_sale_help" or lowered in {"record a sale", "vente", "nouvelle vente"}:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "To record a sale, send: vente BBC 9000\nOr: vente Robe 2 12000",
        )
        return {"ok": True, "action": "sale_help"}

    if button == "list_products" or lowered in {"my products", "mes produits", "show my products"}:
        from app.models.product import Product

        products = db.scalars(
            select(Product).where(Product.store_id == store.id).limit(10)
        ).all()
        if not products:
            _send_text(db, adapter, conversation, from_number, "No products yet.")
        else:
            lines = [f"• {p.name}: {format_xaf(p.price)}" for p in products]
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                "Your products:\n" + "\n".join(lines),
            )
        return {"ok": True, "action": "list_products"}

    parsed = _parse_sale_text(content)
    if parsed:
        product = match_product_by_name(db, store.id, parsed["name"])
        item = {
            "name": product.name if product else parsed["name"],
            "quantity": parsed["quantity"],
            "unit_price": parsed["unit_price"],
            "product_id": str(product.id) if product else None,
        }
        sale = create_sale(db, store, [item])
        conversation.state = ConversationState.GENERAL_ASSISTANCE
        conversation.context = {"last_sale_id": str(sale.id)}
        db.commit()
        body, buttons = _sale_recorded_reply(sale)
        _send_buttons(db, adapter, conversation, from_number, body, buttons)
        return {
            "ok": True,
            "action": "sale_recorded",
            "sale_code": sale.public_code,
            "total": str(sale.total_amount),
        }

    if lowered in {"hello", "hi", "bonjour", "salut", "start"}:
        _send_buttons(
            db,
            adapter,
            conversation,
            from_number,
            "Welcome to Komero. I can record sales and send receipts from WhatsApp.",
            [
                {"id": "record_sale_help", "title": "Record a sale"},
                {"id": "add_product", "title": "Add a product"},
                {"id": "list_products", "title": "My products"},
            ],
        )
        return {"ok": True, "action": "welcome"}

    _send_text(
        db,
        adapter,
        conversation,
        from_number,
        "I did not understand. Try: vente BBC 9000\nOr send hello for the menu.",
    )
    return {"ok": True, "action": "fallback"}
