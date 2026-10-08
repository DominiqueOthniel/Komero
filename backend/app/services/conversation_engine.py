import json
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.models.ai import AIAction, AIActionStatus, AIActionType
from app.models.conversation import (
    Conversation,
    ConversationState,
    ConversationStatus,
    Message,
    MessageDirection,
    MessageType,
)
from app.models.product import Product, ProductStatus
from app.models.store import Store, StoreStatus
from app.models.whatsapp import WhatsAppConnection
from app.schemas.product import ProductCreate, ProductVariantIn
from app.services.money import format_xaf
from app.services.onboarding import activate_store_with_name, find_store_by_merchant_phone
from app.services.products import create_product
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
        if not cleaned.lower().startswith(("vente", "vendre", "sale", "sell")):
            # Avoid treating free-form product descriptions as sales.
            if "fcfa" not in cleaned.lower() and "xaf" not in cleaned.lower():
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

    initial_state = ConversationState.GENERAL_ASSISTANCE
    if store.status == StoreStatus.DRAFT or store.name == "Nouvelle boutique":
        initial_state = ConversationState.CREATING_STORE

    conversation = Conversation(
        store_id=store.id,
        whatsapp_number=whatsapp_number,
        status=ConversationStatus.OPEN,
        state=initial_state,
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


def identify_store(
    db: Session,
    phone_number_id: str | None,
    to_number: str | None,
    from_number: str | None = None,
) -> Store | None:
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
            select(Store).where(
                Store.whatsapp_number.in_([to_number, normalized, f"+{normalized}"])
            )
        )
        if store:
            return store

    if from_number:
        return find_store_by_merchant_phone(db, from_number)
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


def _format_product_draft(draft: dict[str, Any]) -> str:
    lines = ["Product draft:"]
    lines.append(f"Name: {draft.get('name') or '?'}")
    price = draft.get("price")
    lines.append(f"Price: {format_xaf(Decimal(str(price))) if price is not None else '?'}")
    stock = draft.get("stock")
    lines.append(f"Stock: {stock if stock is not None else '?'}")
    variants = draft.get("variants") or []
    if variants:
        sizes = ", ".join(str(v.get("value")) for v in variants if v.get("value"))
        if sizes:
            lines.append(f"Sizes: {sizes}")
    missing = draft.get("missing_fields") or []
    if missing:
        lines.append("Missing: " + ", ".join(missing))
    lines.append("Confirm to publish, Edit to change, or Cancel.")
    return "\n".join(lines)


def _product_confirm_buttons() -> list[dict[str, str]]:
    return [
        {"id": "product_confirm", "title": "Confirm"},
        {"id": "product_edit", "title": "Edit"},
        {"id": "product_cancel", "title": "Cancel"},
    ]


def _log_ai_action(
    db: Session,
    conversation: Conversation,
    action_type: AIActionType,
    input_text: str,
    output: dict[str, Any],
) -> None:
    db.add(
        AIAction(
            conversation_id=conversation.id,
            action_type=action_type,
            input=input_text,
            output=json.dumps(output, ensure_ascii=True),
            status=AIActionStatus.COMPLETED,
        )
    )
    db.commit()


def _start_product_draft(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
    text: str,
) -> dict[str, Any]:
    provider = get_ai_provider()
    draft = provider.extract_product(text, language="fr")
    _log_ai_action(db, conversation, AIActionType.EXTRACT_PRODUCT, text, draft)

    if draft.get("missing_fields"):
        conversation.state = ConversationState.ADDING_PRODUCT
        conversation.context = {"pending_product": draft, "raw_text": text}
        db.commit()
        missing = ", ".join(draft["missing_fields"])
        _send_text(
            db,
            adapter,
            conversation,
            to,
            f"I need more details ({missing}). Example: Robe wax 15000 FCFA, 8 pieces.",
        )
        return {"ok": True, "action": "product_missing_fields", "draft": draft}

    conversation.state = ConversationState.WAITING_PRODUCT_CONFIRMATION
    conversation.context = {"pending_product": draft, "raw_text": text}
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        _format_product_draft(draft),
        _product_confirm_buttons(),
    )
    return {"ok": True, "action": "product_confirm_prompt", "draft": draft}


def _persist_product_from_draft(
    db: Session, store: Store, draft: dict[str, Any]
) -> Product:
    variants = [
        ProductVariantIn(
            name=str(item.get("name") or "size"),
            value=str(item.get("value")),
            stock_quantity=int(item["stock"]) if item.get("stock") is not None else 0,
            price=None,
        )
        for item in (draft.get("variants") or [])
        if item.get("value")
    ]
    payload = ProductCreate(
        name=str(draft["name"]),
        description=draft.get("description"),
        price=Decimal(str(draft["price"])),
        stock_quantity=int(draft["stock"]) if draft.get("stock") is not None else 0,
        status=ProductStatus.PUBLISHED,
        variants=variants,
    )
    return create_product(db, store.id, payload)


def _handle_creating_store(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    from_number: str,
    content: str,
    button: str,
    lowered: str,
) -> dict[str, Any]:
    if button == "start_onboarding" or lowered in {"hello", "hi", "bonjour", "salut", "start"}:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Welcome to Komero. What is your shop name?",
        )
        return {"ok": True, "action": "ask_store_name"}

    if not content:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Send your shop name to finish setup.",
        )
        return {"ok": True, "action": "ask_store_name"}

    if lowered in {"cancel", "annuler"}:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Setup paused. Send your shop name when you are ready.",
        )
        return {"ok": True, "action": "onboarding_paused"}

    store = activate_store_with_name(db, store, content)
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    conversation.context = {}
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        from_number,
        f"Shop ready: {store.name}. You can add products or record sales.",
        [
            {"id": "add_product", "title": "Add a product"},
            {"id": "record_sale_help", "title": "Record a sale"},
            {"id": "list_products", "title": "My products"},
        ],
    )
    return {"ok": True, "action": "store_created", "store": store.name}


def _handle_product_states(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    from_number: str,
    content: str,
    button: str,
    lowered: str,
) -> dict[str, Any] | None:
    state = conversation.state

    if state == ConversationState.ADDING_PRODUCT:
        if button == "product_cancel" or lowered in {"cancel", "annuler"}:
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            conversation.context = {}
            db.commit()
            _send_text(db, adapter, conversation, from_number, "Product creation cancelled.")
            return {"ok": True, "action": "product_cancelled"}
        if not content:
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                "Send the product as text, for example: Robe rouge 12000 FCFA, 5 pieces.",
            )
            return {"ok": True, "action": "add_product_prompt"}
        return _start_product_draft(db, adapter, conversation, from_number, content)

    if state == ConversationState.WAITING_PRODUCT_CONFIRMATION:
        draft = (conversation.context or {}).get("pending_product") or {}
        if button == "product_cancel" or lowered in {"cancel", "annuler"}:
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            conversation.context = {}
            db.commit()
            _send_text(db, adapter, conversation, from_number, "Product creation cancelled.")
            return {"ok": True, "action": "product_cancelled"}

        if button == "product_edit" or lowered in {"edit", "modifier"}:
            conversation.state = ConversationState.EDITING_PRODUCT
            db.commit()
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                "Send the corrected product details in one message.",
            )
            return {"ok": True, "action": "product_edit_prompt"}

        if button == "product_confirm" or lowered in {"confirm", "confirmer", "ok", "oui"}:
            if not draft.get("name") or draft.get("price") is None:
                conversation.state = ConversationState.ADDING_PRODUCT
                db.commit()
                _send_text(
                    db,
                    adapter,
                    conversation,
                    from_number,
                    "Draft incomplete. Send the product again with name and price.",
                )
                return {"ok": False, "action": "product_incomplete"}
            product = _persist_product_from_draft(db, store, draft)
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            conversation.context = {"last_product_id": str(product.id)}
            db.commit()
            _send_buttons(
                db,
                adapter,
                conversation,
                from_number,
                f"Product published: {product.name} ({format_xaf(product.price)}).",
                [
                    {"id": "add_product", "title": "Add another"},
                    {"id": "list_products", "title": "My products"},
                    {"id": "record_sale_help", "title": "Record a sale"},
                ],
            )
            return {
                "ok": True,
                "action": "product_published",
                "product_id": str(product.id),
                "name": product.name,
            }

        _send_buttons(
            db,
            adapter,
            conversation,
            from_number,
            _format_product_draft(draft),
            _product_confirm_buttons(),
        )
        return {"ok": True, "action": "product_confirm_prompt"}

    if state == ConversationState.EDITING_PRODUCT:
        if button == "product_cancel" or lowered in {"cancel", "annuler"}:
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            conversation.context = {}
            db.commit()
            _send_text(db, adapter, conversation, from_number, "Product creation cancelled.")
            return {"ok": True, "action": "product_cancelled"}
        if not content:
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                "Send the corrected product details.",
            )
            return {"ok": True, "action": "product_edit_prompt"}
        return _start_product_draft(db, adapter, conversation, from_number, content)

    return None


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

    if (
        store.status == StoreStatus.DRAFT
        or conversation.state
        in {
            ConversationState.NEW_USER,
            ConversationState.ONBOARDING,
            ConversationState.CREATING_STORE,
        }
    ):
        conversation.state = ConversationState.CREATING_STORE
        db.commit()
        return _handle_creating_store(
            db, adapter, store, conversation, from_number, content, button, lowered
        )

    product_result = _handle_product_states(
        db, adapter, store, conversation, from_number, content, button, lowered
    )
    if product_result is not None:
        return product_result

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
        conversation.context = {}
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Send the product as text, for example: Robe rouge 12000 FCFA, 5 pieces.",
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

    if content.lower().startswith(("vente ", "vendre ", "sale ", "sell ")):
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
            "Welcome to Komero. I can add products, record sales, and send receipts.",
            [
                {"id": "add_product", "title": "Add a product"},
                {"id": "record_sale_help", "title": "Record a sale"},
                {"id": "list_products", "title": "My products"},
            ],
        )
        return {"ok": True, "action": "welcome"}

    # Natural language product intent without pressing the button.
    if any(
        token in lowered
        for token in ("produit", "product", "ajouter", "j'ai", "stock", "fcfa", "xaf")
    ) and not lowered.startswith(("vente ", "vendre ", "sale ", "sell ")):
        return _start_product_draft(db, adapter, conversation, from_number, content)

    _send_text(
        db,
        adapter,
        conversation,
        from_number,
        "I did not understand. Try: vente BBC 9000\nOr describe a product with price in FCFA.\nOr send hello for the menu.",
    )
    return {"ok": True, "action": "fallback"}
