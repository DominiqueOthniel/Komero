import json
import re
import shutil
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
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
from app.schemas.product import ProductCreate, ProductImageIn, ProductVariantIn
from app.services.catalog import product_page_url, public_media_url, shop_catalog_url
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

PRODUCT_MEDIA_DIR = Path(__file__).resolve().parents[2] / "storage" / "products"

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


def _send_catalog(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    store: Store,
    to: str,
    intro: str | None = None,
) -> None:
    url = shop_catalog_url(store)
    body = intro or f"Catalog for {store.name}."
    result = adapter.send_cta_url(
        to,
        body,
        button_text="Open catalog",
        url=url,
    )
    _store_message(
        db,
        conversation,
        MessageDirection.OUTBOUND,
        f"{body}\n{url}",
        MessageType.SYSTEM,
        whatsapp_message_id=str(result.get("id") or ""),
        media_url=url,
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
    body = f"Vente enregistree : {sale.public_code}."
    buttons = [
        {"id": f"receipt:{sale.public_code}", "title": "Recu PDF"},
        {"id": "add_product", "title": "Add a product"},
        {"id": "more_actions", "title": "More actions"},
    ]
    return body, buttons


def _ask_receipt_name(sale) -> tuple[str, list[dict[str, str]]]:
    item_label = "1 article" if sale.item_count == 1 else f"{sale.item_count} articles"
    body = (
        f"Recu pour la vente {sale.public_code} : {item_label}, {format_xaf(sale.total_amount)}. "
        "Au nom de qui ? Ecrivez le nom du client, ou tapez Sans nom."
    )
    buttons = [
        {"id": f"receipt_noname:{sale.public_code}", "title": "Sans nom"},
        {"id": "receipt_cancel", "title": "Annuler"},
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
    pdf_path = Path(receipt.pdf_path or "")
    if not pdf_path.exists():
        from app.models.sale import Sale
        from app.services.receipts import build_receipt_pdf
        from sqlalchemy.orm import joinedload

        sale_full = db.scalar(
            select(Sale).options(joinedload(Sale.items)).where(Sale.id == sale.id)
        )
        if sale_full:
            pdf_path = Path(__file__).resolve().parents[2] / "storage" / "receipts" / (
                f"Receipt-{receipt.number}.pdf"
            )
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            build_receipt_pdf(store, sale_full, receipt, pdf_path)
            receipt.pdf_path = str(pdf_path)
            db.commit()

    verify = verification_url(receipt.number, receipt.verification_key)
    filename = f"Recu-{receipt.number}.pdf"
    caption = (
        f"Recu {receipt.number} · {format_xaf(sale.total_amount)}. "
        f"Verification : {verify}"
    )
    sent_pdf = False
    if pdf_path.exists():
        try:
            result = adapter.send_document(
                to,
                document_path=str(pdf_path),
                filename=filename,
                caption=caption,
            )
            _store_message(
                db,
                conversation,
                MessageDirection.OUTBOUND,
                caption,
                MessageType.DOCUMENT,
                whatsapp_message_id=str(result.get("id") or ""),
                media_url=verify,
            )
            sent_pdf = True
        except Exception:
            sent_pdf = False

    if not sent_pdf:
        _send_text(
            db,
            adapter,
            conversation,
            to,
            f"Recu {receipt.number} pret en ligne (PDF) : {verify}",
        )
    _send_text(
        db,
        adapter,
        conversation,
        to,
        f"Partagez ce lien de verification avec votre client :\n{verify}",
    )
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    conversation.context = {"last_receipt_number": receipt.number}
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
    *,
    image_path: str | None = None,
) -> dict[str, Any]:
    provider = get_ai_provider()
    if image_path:
        draft = provider.extract_product_from_image(
            image_path=image_path, caption=text, language="fr"
        )
    else:
        draft = provider.extract_product(text, language="fr")
    _log_ai_action(db, conversation, AIActionType.EXTRACT_PRODUCT, text or image_path or "", draft)

    if draft.get("missing_fields"):
        conversation.state = ConversationState.ADDING_PRODUCT
        conversation.context = {
            "pending_product": draft,
            "raw_text": text,
            "image_path": image_path or draft.get("image_path"),
        }
        db.commit()
        missing = ", ".join(draft["missing_fields"])
        hint = (
            "Send a photo with a caption, or text like: Robe wax 15000 FCFA, 8 pieces."
            if image_path
            else "Example: Robe wax 15000 FCFA, 8 pieces. You can also send a product photo."
        )
        _send_text(
            db,
            adapter,
            conversation,
            to,
            f"I need more details ({missing}). {hint}",
        )
        return {"ok": True, "action": "product_missing_fields", "draft": draft}

    conversation.state = ConversationState.WAITING_PRODUCT_CONFIRMATION
    conversation.context = {
        "pending_product": draft,
        "raw_text": text,
        "image_path": image_path or draft.get("image_path"),
    }
    db.commit()
    body = _format_product_draft(draft)
    if image_path or draft.get("image_path"):
        body = "Photo received.\n" + body
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        body,
        _product_confirm_buttons(),
    )
    return {"ok": True, "action": "product_confirm_prompt", "draft": draft}


def _persist_product_from_draft(
    db: Session, store: Store, draft: dict[str, Any], image_path: str | None = None
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
    images: list[ProductImageIn] = []
    source_image = image_path or draft.get("image_path")
    if source_image and Path(source_image).exists():
        PRODUCT_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(source_image).suffix or ".jpg"
        filename = f"{uuid.uuid4().hex}{suffix}"
        dest = PRODUCT_MEDIA_DIR / filename
        shutil.copy2(source_image, dest)
        images.append(
            ProductImageIn(
                image_url=public_media_url("products", filename),
                position=0,
            )
        )
    payload = ProductCreate(
        name=str(draft["name"]),
        description=draft.get("description"),
        price=Decimal(str(draft["price"])),
        stock_quantity=int(draft["stock"]) if draft.get("stock") is not None else 0,
        status=ProductStatus.PUBLISHED,
        variants=variants,
        images=images,
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
            {"id": "view_catalog", "title": "Catalog link"},
        ],
    )
    _send_catalog(
        db,
        adapter,
        conversation,
        store,
        from_number,
        intro=f"Here is your public catalog for {store.name}.",
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
    *,
    image_path: str | None = None,
) -> dict[str, Any] | None:
    state = conversation.state

    if state == ConversationState.ADDING_PRODUCT:
        if button == "product_cancel" or lowered in {"cancel", "annuler"}:
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            conversation.context = {}
            db.commit()
            _send_text(db, adapter, conversation, from_number, "Product creation cancelled.")
            return {"ok": True, "action": "product_cancelled"}
        if image_path:
            return _start_product_draft(
                db, adapter, conversation, from_number, content, image_path=image_path
            )
        if not content:
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                "Send product text or a photo with caption. Example: Robe rouge 12000 FCFA, 5 pieces.",
            )
            return {"ok": True, "action": "add_product_prompt"}
        prior_image = (conversation.context or {}).get("image_path")
        return _start_product_draft(
            db,
            adapter,
            conversation,
            from_number,
            content,
            image_path=prior_image,
        )

    if state == ConversationState.WAITING_PRODUCT_CONFIRMATION:
        draft = (conversation.context or {}).get("pending_product") or {}
        image_path = image_path or (conversation.context or {}).get("image_path")
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
                "Send the corrected details as text, or a new photo with caption.",
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
            product = _persist_product_from_draft(db, store, draft, image_path=image_path)
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
                    {"id": "view_catalog", "title": "Catalog link"},
                    {"id": "record_sale_help", "title": "Record a sale"},
                ],
            )
            _send_catalog(
                db,
                adapter,
                conversation,
                store,
                from_number,
                intro=f"Catalog updated. Product page: {product_page_url(store, str(product.id))}",
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
        if image_path:
            return _start_product_draft(
                db, adapter, conversation, from_number, content, image_path=image_path
            )
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


def _handle_media_message(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    from_number: str,
    *,
    media_id: str,
    media_kind: str,
    mime_type: str | None,
    caption: str,
) -> dict[str, Any]:
    if media_kind == "audio":
        conversation.state = ConversationState.ADDING_PRODUCT
        conversation.context = {
            **(conversation.context or {}),
            "pending_voice_media_id": media_id,
        }
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Voice note received. For now, reply with the product as text "
            "(name + price in FCFA), or send a photo with a caption. Full voice understanding comes next.",
        )
        return {"ok": True, "action": "voice_received_pending_text"}

    if media_kind == "image":
        suffix = ".jpg"
        if mime_type and "png" in mime_type:
            suffix = ".png"
        elif mime_type and "webp" in mime_type:
            suffix = ".webp"
        try:
            image_path = adapter.download_media(media_id, suffix=suffix)
        except Exception:
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                "I could not download that photo. Please send it again, or describe the product in text.",
            )
            return {"ok": False, "action": "image_download_failed"}
        conversation.state = ConversationState.ADDING_PRODUCT
        db.commit()
        return _start_product_draft(
            db,
            adapter,
            conversation,
            from_number,
            caption,
            image_path=image_path,
        )

    return {"ok": False, "action": "unsupported_media"}


def handle_incoming_message(
    db: Session,
    adapter: WhatsAppAdapter,
    *,
    store: Store,
    from_number: str,
    text: str,
    button_id: str | None = None,
    whatsapp_message_id: str | None = None,
    media_id: str | None = None,
    media_kind: str | None = None,
    mime_type: str | None = None,
) -> dict[str, Any]:
    conversation = _get_or_create_conversation(db, store, from_number)
    inbound = text or button_id or media_kind or ""
    message_type = MessageType.BUTTON if button_id else MessageType.TEXT
    if media_kind == "image":
        message_type = MessageType.IMAGE
    elif media_kind == "audio":
        message_type = MessageType.AUDIO
    _store_message(
        db,
        conversation,
        MessageDirection.INBOUND,
        inbound,
        message_type,
        whatsapp_message_id=whatsapp_message_id,
        media_url=media_id,
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

    if media_id and media_kind in {"image", "audio"}:
        return _handle_media_message(
            db,
            adapter,
            store,
            conversation,
            from_number,
            media_id=media_id,
            media_kind=media_kind,
            mime_type=mime_type,
            caption=content,
        )

    product_result = _handle_product_states(
        db,
        adapter,
        store,
        conversation,
        from_number,
        content,
        button,
        lowered,
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
            _send_text(db, adapter, conversation, from_number, "Recu annule.")
            return {"ok": True, "action": "receipt_cancelled"}

        if sale and (
            button.startswith("receipt_noname:")
            or lowered in {"no name", "sans nom", "noname", "sans-nom"}
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
            "Ecrivez le nom du client, ou tapez Sans nom.",
        )
        return {"ok": True, "action": "awaiting_receipt_name"}

    receipt_text_match = re.match(
        r"^(?:receipt|recu|reçu|pdf)\s+([A-Za-z0-9\-]+)$",
        content,
        flags=re.IGNORECASE,
    )
    if button.startswith("receipt:") or receipt_text_match:
        code = (
            button.split(":", 1)[1]
            if button.startswith("receipt:")
            else receipt_text_match.group(1)
        )
        sale = get_sale_by_code(db, store.id, code.strip())
        if not sale:
            _send_text(db, adapter, conversation, from_number, "Vente introuvable.")
            return {"ok": False, "action": "sale_not_found"}
        conversation.state = ConversationState.WAITING_RECEIPT_NAME
        conversation.context = {"pending_sale_id": str(sale.id)}
        db.commit()
        body, buttons = _ask_receipt_name(sale)
        _send_buttons(db, adapter, conversation, from_number, body, buttons)
        return {"ok": True, "action": "ask_receipt_name", "sale_code": sale.public_code}

    if button == "view_catalog" or lowered in {
        "catalog",
        "catalogue",
        "catalog link",
        "lien catalogue",
        "ma boutique",
        "my shop",
    }:
        _send_catalog(
            db,
            adapter,
            conversation,
            store,
            from_number,
            intro=f"Public catalog for {store.name}.",
        )
        return {"ok": True, "action": "catalog_link", "url": shop_catalog_url(store)}

    if button == "add_product" or lowered in {"add a product", "ajouter produit", "add product"}:
        conversation.state = ConversationState.ADDING_PRODUCT
        conversation.context = {}
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            "Send product text, a photo with caption, or a voice note then the price in text.\n"
            "Example: Robe rouge 12000 FCFA, 5 pieces.",
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
                {"id": "add_product", "title": "Add a product"},
                {"id": "view_catalog", "title": "Catalog link"},
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
            "Pour enregistrer une vente : vente BBC 9000\nOu : vente Robe 2 12000\n"
            "Puis tapez Recu PDF pour recevoir le document.",
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
        _send_catalog(
            db,
            adapter,
            conversation,
            store,
            from_number,
            intro="Open the full catalog online.",
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
            "Bienvenue sur Komero. Ajoutez des produits (texte/photo), enregistrez des ventes, et envoyez des recus PDF.",
            [
                {"id": "add_product", "title": "Add a product"},
                {"id": "view_catalog", "title": "Catalog link"},
                {"id": "record_sale_help", "title": "Record a sale"},
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
        "Je n'ai pas compris.\n"
        "Essayez : vente BBC 9000\n"
        "Ou envoyez une photo produit avec le prix en legende\n"
        "Ou envoyez bonjour pour le menu.",
    )
    return {"ok": True, "action": "fallback"}
