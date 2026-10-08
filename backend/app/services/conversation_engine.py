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
from app.services.bot_copy import buttons, normalize_lang, t
from app.services.catalog import product_page_url, public_media_url, shop_catalog_url
from app.services.money import format_xaf
from app.services.onboarding import activate_store_with_name, find_store_by_merchant_phone
from app.services.products import create_product, delete_product, get_product, list_products
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
]

MENU_TRIGGERS = {
    "menu",
    "0",
    "accueil",
    "home",
    "start",
    "bonjour",
    "salut",
    "hello",
    "hi",
}
CANCEL_TRIGGERS = {"cancel", "annuler", "non", "no"}


def _normalize_button(value: str) -> str:
    return value.strip().lower()


def _lang(conversation: Conversation) -> str | None:
    return normalize_lang((conversation.context or {}).get("lang"))


def _set_context(conversation: Conversation, **kwargs: Any) -> None:
    lang = _lang(conversation)
    ctx = dict(kwargs)
    if lang:
        ctx["lang"] = lang
    conversation.context = ctx


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
    button_list: list[dict[str, str]],
) -> None:
    result = adapter.send_buttons(to, body, button_list)
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
    lang = _lang(conversation)
    url = shop_catalog_url(store)
    body = intro or t("catalog_intro", lang, name=store.name)
    result = adapter.send_cta_url(
        to,
        body,
        button_text=t("btn_open_catalog", lang)[:20],
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


def _ask_language(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
) -> dict[str, Any]:
    conversation.state = ConversationState.CHOOSING_LANGUAGE
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        t("ask_language", "fr"),
        buttons("fr", ("lang_fr", "btn_fr"), ("lang_en", "btn_en")),
    )
    return {"ok": True, "action": "choose_language"}


def _send_main_menu(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    to: str,
) -> None:
    lang = _lang(conversation)
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    _set_context(conversation)
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        t("main_menu", lang, name=store.name),
        buttons(
            lang,
            ("menu_products", "btn_products"),
            ("menu_sales", "btn_sales"),
            ("menu_more", "btn_more"),
        ),
    )


def _send_products_menu(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
) -> None:
    lang = _lang(conversation)
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        t("products_menu", lang),
        buttons(
            lang,
            ("add_product", "btn_add"),
            ("list_products", "btn_list"),
            ("delete_product", "btn_delete"),
        ),
    )


def _send_sales_menu(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
) -> None:
    lang = _lang(conversation)
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        t("sales_menu", lang),
        buttons(
            lang,
            ("record_sale_help", "btn_new_sale"),
            ("receipt_last", "btn_receipt"),
            ("main_menu", "btn_back"),
        ),
    )


def _send_more_menu(
    db: Session,
    adapter: WhatsAppAdapter,
    conversation: Conversation,
    to: str,
) -> None:
    lang = _lang(conversation)
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        t("more_menu", lang),
        buttons(
            lang,
            ("view_catalog", "btn_catalog"),
            ("change_language", "btn_language"),
            ("help", "btn_help"),
        ),
    )


def _format_product_draft(draft: dict[str, Any], lang: str | None) -> str:
    lines = [t("product_draft_title", lang)]
    lines.append(f"{t('label_name', lang)}: {draft.get('name') or '?'}")
    price = draft.get("price")
    lines.append(
        f"{t('label_price', lang)}: "
        f"{format_xaf(Decimal(str(price))) if price is not None else '?'}"
    )
    stock = draft.get("stock")
    lines.append(
        f"{t('label_stock', lang)}: {stock if stock is not None else '?'}"
    )
    variants = draft.get("variants") or []
    if variants:
        sizes = ", ".join(str(v.get("value")) for v in variants if v.get("value"))
        if sizes:
            lines.append(f"{t('label_sizes', lang)}: {sizes}")
    missing = draft.get("missing_fields") or []
    if missing:
        lines.append(f"{t('label_missing', lang)}: " + ", ".join(missing))
    lines.append(t("product_draft_footer", lang))
    return "\n".join(lines)


def _product_confirm_buttons(lang: str | None) -> list[dict[str, str]]:
    return buttons(
        lang,
        ("product_confirm", "btn_confirm"),
        ("product_edit", "btn_edit"),
        ("product_cancel", "btn_cancel"),
    )


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
    lang = _lang(conversation) or "fr"
    provider = get_ai_provider()
    if image_path:
        draft = provider.extract_product_from_image(
            image_path=image_path, caption=text, language=lang
        )
    else:
        draft = provider.extract_product(text, language=lang)
    _log_ai_action(
        db, conversation, AIActionType.EXTRACT_PRODUCT, text or image_path or "", draft
    )

    if draft.get("missing_fields"):
        conversation.state = ConversationState.ADDING_PRODUCT
        _set_context(
            conversation,
            pending_product=draft,
            raw_text=text,
            image_path=image_path or draft.get("image_path"),
        )
        db.commit()
        missing = ", ".join(draft["missing_fields"])
        hint = t(
            "product_hint_photo" if image_path else "product_hint_text",
            lang,
        )
        _send_text(
            db,
            adapter,
            conversation,
            to,
            t("product_missing", lang, missing=missing, hint=hint),
        )
        return {"ok": True, "action": "product_missing_fields", "draft": draft}

    conversation.state = ConversationState.WAITING_PRODUCT_CONFIRMATION
    _set_context(
        conversation,
        pending_product=draft,
        raw_text=text,
        image_path=image_path or draft.get("image_path"),
    )
    db.commit()
    body = _format_product_draft(draft, lang)
    if image_path or draft.get("image_path"):
        body = t("product_photo_received", lang) + "\n" + body
    _send_buttons(
        db,
        adapter,
        conversation,
        to,
        body,
        _product_confirm_buttons(lang),
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


def _issue_receipt(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    to: str,
    sale,
    customer_name: str | None,
) -> None:
    lang = _lang(conversation)
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
            pdf_path = (
                Path(__file__).resolve().parents[2]
                / "storage"
                / "receipts"
                / f"Receipt-{receipt.number}.pdf"
            )
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            build_receipt_pdf(store, sale_full, receipt, pdf_path)
            receipt.pdf_path = str(pdf_path)
            db.commit()

    verify = verification_url(receipt.number, receipt.verification_key)
    filename = f"Recu-{receipt.number}.pdf"
    caption = t(
        "receipt_caption",
        lang,
        number=receipt.number,
        total=format_xaf(sale.total_amount),
        verify=verify,
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
            t("receipt_online", lang, number=receipt.number, verify=verify),
        )
    _send_text(
        db,
        adapter,
        conversation,
        to,
        t("receipt_share", lang, verify=verify),
    )
    conversation.state = ConversationState.GENERAL_ASSISTANCE
    _set_context(
        conversation,
        last_receipt_number=receipt.number,
        last_sale_id=str(sale.id),
    )
    db.commit()


def _handle_language_choice(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    from_number: str,
    content: str,
    button: str,
) -> dict[str, Any] | None:
    chosen = None
    if button == "lang_fr" or normalize_lang(content) == "fr":
        chosen = "fr"
    elif button == "lang_en" or normalize_lang(content) == "en":
        chosen = "en"
    elif button == "change_language" or content.lower() in {
        "langue",
        "language",
        "lang",
    }:
        return _ask_language(db, adapter, conversation, from_number)

    if conversation.state != ConversationState.CHOOSING_LANGUAGE and chosen is None:
        return None

    if chosen is None:
        return _ask_language(db, adapter, conversation, from_number)

    conversation.context = {**(conversation.context or {}), "lang": chosen}
    db.commit()
    _send_text(db, adapter, conversation, from_number, t("lang_saved", chosen))

    if store.status == StoreStatus.DRAFT or store.name == "Nouvelle boutique":
        conversation.state = ConversationState.CREATING_STORE
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("ask_store_name", chosen),
        )
        return {"ok": True, "action": "ask_store_name", "lang": chosen}

    _send_main_menu(db, adapter, store, conversation, from_number)
    return {"ok": True, "action": "welcome", "lang": chosen}


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
    lang = _lang(conversation)
    if not lang:
        return _ask_language(db, adapter, conversation, from_number)

    if button == "start_onboarding" or lowered in MENU_TRIGGERS:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("ask_store_name", lang),
        )
        return {"ok": True, "action": "ask_store_name"}

    if not content:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("ask_store_name_again", lang),
        )
        return {"ok": True, "action": "ask_store_name"}

    if lowered in CANCEL_TRIGGERS:
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("onboarding_paused", lang),
        )
        return {"ok": True, "action": "onboarding_paused"}

    store = activate_store_with_name(db, store, content)
    _send_text(
        db,
        adapter,
        conversation,
        from_number,
        t("store_ready", lang, name=store.name),
    )
    _send_main_menu(db, adapter, store, conversation, from_number)
    _send_catalog(
        db,
        adapter,
        conversation,
        store,
        from_number,
        intro=t("catalog_intro", lang, name=store.name),
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
    lang = _lang(conversation)
    state = conversation.state

    if state == ConversationState.ADDING_PRODUCT:
        if button == "product_cancel" or lowered in CANCEL_TRIGGERS:
            _send_text(
                db, adapter, conversation, from_number, t("product_cancelled", lang)
            )
            _send_products_menu(db, adapter, conversation, from_number)
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
                t("add_product_prompt", lang),
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
        if button == "product_cancel" or lowered in CANCEL_TRIGGERS:
            _send_text(
                db, adapter, conversation, from_number, t("product_cancelled", lang)
            )
            _send_products_menu(db, adapter, conversation, from_number)
            return {"ok": True, "action": "product_cancelled"}

        if button == "product_edit" or lowered in {"edit", "modifier"}:
            conversation.state = ConversationState.EDITING_PRODUCT
            db.commit()
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                t("product_edit_prompt", lang),
            )
            return {"ok": True, "action": "product_edit_prompt"}

        if button == "product_confirm" or lowered in {
            "confirm",
            "confirmer",
            "ok",
            "oui",
            "yes",
        }:
            if not draft.get("name") or draft.get("price") is None:
                conversation.state = ConversationState.ADDING_PRODUCT
                db.commit()
                _send_text(
                    db,
                    adapter,
                    conversation,
                    from_number,
                    t("product_incomplete", lang),
                )
                return {"ok": False, "action": "product_incomplete"}
            product = _persist_product_from_draft(
                db, store, draft, image_path=image_path
            )
            _set_context(conversation, last_product_id=str(product.id))
            db.commit()
            _send_buttons(
                db,
                adapter,
                conversation,
                from_number,
                t(
                    "product_published",
                    lang,
                    name=product.name,
                    price=format_xaf(product.price),
                ),
                buttons(
                    lang,
                    ("add_product", "btn_add"),
                    ("view_catalog", "btn_catalog"),
                    ("main_menu", "btn_menu"),
                ),
            )
            _send_catalog(
                db,
                adapter,
                conversation,
                store,
                from_number,
                intro=t(
                    "catalog_updated",
                    lang,
                    url=product_page_url(store, str(product.id)),
                ),
            )
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            db.commit()
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
            _format_product_draft(draft, lang),
            _product_confirm_buttons(lang),
        )
        return {"ok": True, "action": "product_confirm_prompt"}

    if state == ConversationState.EDITING_PRODUCT:
        if button == "product_cancel" or lowered in CANCEL_TRIGGERS:
            _send_text(
                db, adapter, conversation, from_number, t("product_cancelled", lang)
            )
            _send_products_menu(db, adapter, conversation, from_number)
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
                t("product_edit_prompt", lang),
            )
            return {"ok": True, "action": "product_edit_prompt"}
        return _start_product_draft(db, adapter, conversation, from_number, content)

    return None


def _handle_delete_states(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    from_number: str,
    content: str,
    button: str,
    lowered: str,
) -> dict[str, Any] | None:
    lang = _lang(conversation)

    if conversation.state == ConversationState.CONFIRMING_DELETE:
        product_id = (conversation.context or {}).get("pending_delete_id")
        if button in {"delete_no", "main_menu"} or lowered in CANCEL_TRIGGERS | {
            "non",
            "no",
        }:
            _send_text(
                db, adapter, conversation, from_number, t("delete_cancelled", lang)
            )
            _send_products_menu(db, adapter, conversation, from_number)
            return {"ok": True, "action": "delete_cancelled"}
        if button == "delete_yes" or lowered in {"oui", "yes", "ok", "confirm", "confirmer"}:
            product = (
                get_product(db, store.id, uuid.UUID(product_id)) if product_id else None
            )
            if not product:
                _send_text(
                    db, adapter, conversation, from_number, t("delete_not_found", lang)
                )
                _send_products_menu(db, adapter, conversation, from_number)
                return {"ok": False, "action": "delete_not_found"}
            name = product.name
            delete_product(db, product)
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                t("delete_done", lang, name=name),
            )
            _send_products_menu(db, adapter, conversation, from_number)
            return {"ok": True, "action": "product_deleted", "name": name}
        product = get_product(db, store.id, uuid.UUID(product_id)) if product_id else None
        if product:
            _send_buttons(
                db,
                adapter,
                conversation,
                from_number,
                t(
                    "delete_confirm",
                    lang,
                    name=product.name,
                    price=format_xaf(product.price),
                ),
                buttons(
                    lang,
                    ("delete_yes", "btn_yes_delete"),
                    ("delete_no", "btn_no"),
                    ("main_menu", "btn_menu"),
                ),
            )
        return {"ok": True, "action": "awaiting_delete_confirm"}

    if conversation.state != ConversationState.DELETING_PRODUCT:
        return None

    if button == "main_menu" or lowered in MENU_TRIGGERS | CANCEL_TRIGGERS:
        _send_text(db, adapter, conversation, from_number, t("delete_cancelled", lang))
        _send_main_menu(db, adapter, store, conversation, from_number)
        return {"ok": True, "action": "delete_cancelled"}

    products = list_products(db, store.id)[:10]
    chosen = None
    if content.isdigit():
        index = int(content) - 1
        if 0 <= index < len(products):
            chosen = products[index]
    if chosen is None and content:
        chosen = match_product_by_name(db, store.id, content)

    if not chosen:
        lines = "\n".join(
            f"{i}. {p.name} · {format_xaf(p.price)}" for i, p in enumerate(products, 1)
        )
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("delete_not_found", lang)
            + "\n"
            + t("delete_prompt", lang, lines=lines or "-"),
        )
        return {"ok": False, "action": "delete_not_found"}

    conversation.state = ConversationState.CONFIRMING_DELETE
    _set_context(conversation, pending_delete_id=str(chosen.id))
    db.commit()
    _send_buttons(
        db,
        adapter,
        conversation,
        from_number,
        t(
            "delete_confirm",
            lang,
            name=chosen.name,
            price=format_xaf(chosen.price),
        ),
        buttons(
            lang,
            ("delete_yes", "btn_yes_delete"),
            ("delete_no", "btn_no"),
            ("main_menu", "btn_menu"),
        ),
    )
    return {"ok": True, "action": "confirm_delete", "product_id": str(chosen.id)}


def _start_delete_flow(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    to: str,
) -> dict[str, Any]:
    lang = _lang(conversation)
    products = list_products(db, store.id)[:10]
    if not products:
        _send_text(db, adapter, conversation, to, t("no_products", lang))
        _send_products_menu(db, adapter, conversation, to)
        return {"ok": True, "action": "no_products"}
    lines = "\n".join(
        f"{i}. {p.name} · {format_xaf(p.price)}" for i, p in enumerate(products, 1)
    )
    conversation.state = ConversationState.DELETING_PRODUCT
    _set_context(conversation)
    db.commit()
    _send_text(
        db,
        adapter,
        conversation,
        to,
        t("delete_prompt", lang, lines=lines),
    )
    return {"ok": True, "action": "delete_prompt"}


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
    lang = _lang(conversation)
    if media_kind == "audio":
        conversation.state = ConversationState.ADDING_PRODUCT
        _set_context(conversation, pending_voice_media_id=media_id)
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("voice_pending", lang),
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
                t("image_failed", lang),
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


def _begin_receipt(
    db: Session,
    adapter: WhatsAppAdapter,
    store: Store,
    conversation: Conversation,
    from_number: str,
    sale,
) -> dict[str, Any]:
    lang = _lang(conversation)
    conversation.state = ConversationState.WAITING_RECEIPT_NAME
    _set_context(conversation, pending_sale_id=str(sale.id), last_sale_id=str(sale.id))
    db.commit()
    item_label = (
        "1 article" if sale.item_count == 1 else f"{sale.item_count} articles"
        if lang != "en"
        else ("1 item" if sale.item_count == 1 else f"{sale.item_count} items")
    )
    body = t(
        "ask_receipt_name",
        lang,
        code=sale.public_code,
        items=item_label,
        total=format_xaf(sale.total_amount),
    )
    _send_buttons(
        db,
        adapter,
        conversation,
        from_number,
        body,
        [
            {
                "id": f"receipt_noname:{sale.public_code}",
                "title": t("btn_no_name", lang)[:20],
            },
            {"id": "receipt_cancel", "title": t("btn_cancel", lang)[:20]},
            {"id": "main_menu", "title": t("btn_menu", lang)[:20]},
        ],
    )
    return {"ok": True, "action": "ask_receipt_name", "sale_code": sale.public_code}


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
    lang = _lang(conversation)

    # Global language change / first-time language pick.
    if (
        conversation.state == ConversationState.CHOOSING_LANGUAGE
        or button in {"lang_fr", "lang_en", "change_language"}
        or lowered in {"langue", "language", "lang"}
        or (not lang and button not in {"lang_fr", "lang_en"})
    ):
        # Allow mid-flow product confirm without forcing language again if already set.
        if not lang or conversation.state == ConversationState.CHOOSING_LANGUAGE or button in {
            "lang_fr",
            "lang_en",
            "change_language",
        } or lowered in {"langue", "language", "lang"}:
            lang_result = _handle_language_choice(
                db, adapter, store, conversation, from_number, content, button
            )
            if lang_result is not None:
                return lang_result

    lang = _lang(conversation)
    if not lang:
        return _ask_language(db, adapter, conversation, from_number)

    # Global menu escape hatch.
    if button == "main_menu" or lowered in MENU_TRIGGERS:
        _send_main_menu(db, adapter, store, conversation, from_number)
        return {"ok": True, "action": "welcome"}

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

    delete_result = _handle_delete_states(
        db, adapter, store, conversation, from_number, content, button, lowered
    )
    if delete_result is not None:
        return delete_result

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
        if button == "receipt_cancel" or lowered in CANCEL_TRIGGERS:
            _send_text(
                db, adapter, conversation, from_number, t("receipt_cancelled", lang)
            )
            _send_sales_menu(db, adapter, conversation, from_number)
            return {"ok": True, "action": "receipt_cancelled"}

        if sale and (
            button.startswith("receipt_noname:")
            or lowered in {"no name", "sans nom", "noname", "sans-nom"}
        ):
            _issue_receipt(db, adapter, store, conversation, from_number, sale, None)
            _send_main_menu(db, adapter, store, conversation, from_number)
            return {"ok": True, "action": "receipt_sent", "receipt": True}

        if sale and content:
            _issue_receipt(db, adapter, store, conversation, from_number, sale, content)
            _send_main_menu(db, adapter, store, conversation, from_number)
            return {"ok": True, "action": "receipt_sent", "receipt": True}

        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("receipt_name_prompt", lang),
        )
        return {"ok": True, "action": "awaiting_receipt_name"}

    # Nested menus.
    if button == "menu_products":
        _send_products_menu(db, adapter, conversation, from_number)
        return {"ok": True, "action": "products_menu"}

    if button == "menu_sales":
        _send_sales_menu(db, adapter, conversation, from_number)
        return {"ok": True, "action": "sales_menu"}

    if button == "menu_more":
        _send_more_menu(db, adapter, conversation, from_number)
        return {"ok": True, "action": "more_menu"}

    if button == "help" or lowered in {"aide", "help", "?"}:
        _send_text(db, adapter, conversation, from_number, t("help", lang))
        _send_main_menu(db, adapter, store, conversation, from_number)
        return {"ok": True, "action": "help"}

    if button == "view_catalog" or lowered in {
        "catalog",
        "catalogue",
        "ma boutique",
        "my shop",
    }:
        _send_catalog(db, adapter, store=store, conversation=conversation, to=from_number)
        _send_more_menu(db, adapter, conversation, from_number)
        return {"ok": True, "action": "catalog_link", "url": shop_catalog_url(store)}

    if button == "add_product" or lowered in {
        "add a product",
        "ajouter produit",
        "add product",
        "ajouter",
    }:
        conversation.state = ConversationState.ADDING_PRODUCT
        _set_context(conversation)
        db.commit()
        _send_text(
            db,
            adapter,
            conversation,
            from_number,
            t("add_product_prompt", lang),
        )
        return {"ok": True, "action": "add_product_prompt"}

    if button == "list_products" or lowered in {
        "my products",
        "mes produits",
        "liste",
        "list",
    }:
        products = list_products(db, store.id)[:10]
        if not products:
            _send_text(db, adapter, conversation, from_number, t("no_products", lang))
        else:
            lines = "\n".join(
                f"• {p.name}: {format_xaf(p.price)}" for p in products
            )
            _send_text(
                db,
                adapter,
                conversation,
                from_number,
                t("products_list", lang, lines=lines),
            )
        _send_products_menu(db, adapter, conversation, from_number)
        return {"ok": True, "action": "list_products"}

    if button == "delete_product" or lowered in {
        "supprimer",
        "delete",
        "supprimer produit",
        "delete product",
    }:
        return _start_delete_flow(db, adapter, store, conversation, from_number)

    if button == "record_sale_help" or lowered in {
        "record a sale",
        "nouvelle vente",
        "new sale",
    }:
        conversation.state = ConversationState.RECORDING_SALE
        db.commit()
        _send_text(db, adapter, conversation, from_number, t("sale_help", lang))
        return {"ok": True, "action": "sale_help"}

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
            _send_text(
                db, adapter, conversation, from_number, t("sale_not_found", lang)
            )
            return {"ok": False, "action": "sale_not_found"}
        return _begin_receipt(db, adapter, store, conversation, from_number, sale)

    if button == "receipt_last":
        from app.services.sales import list_sales

        sale_id = (conversation.context or {}).get("last_sale_id")
        sale = get_sale(db, uuid.UUID(sale_id)) if sale_id else None
        if not sale:
            sales = list_sales(db, store.id, limit=1)
            sale = sales[0] if sales else None
        if not sale:
            _send_text(db, adapter, conversation, from_number, t("no_last_sale", lang))
            _send_sales_menu(db, adapter, conversation, from_number)
            return {"ok": False, "action": "no_last_sale"}
        return _begin_receipt(db, adapter, store, conversation, from_number, sale)

    if content.lower().startswith(("vente ", "vendre ", "sale ", "sell ")) or (
        conversation.state == ConversationState.RECORDING_SALE and content
    ):
        parsed = _parse_sale_text(
            content
            if content.lower().startswith(("vente ", "vendre ", "sale ", "sell "))
            else f"vente {content}"
        )
        if parsed:
            product = match_product_by_name(db, store.id, parsed["name"])
            item = {
                "name": product.name if product else parsed["name"],
                "quantity": parsed["quantity"],
                "unit_price": parsed["unit_price"],
                "product_id": str(product.id) if product else None,
            }
            sale = create_sale(db, store, [item])
            _set_context(conversation, last_sale_id=str(sale.id))
            conversation.state = ConversationState.GENERAL_ASSISTANCE
            db.commit()
            _send_buttons(
                db,
                adapter,
                conversation,
                from_number,
                t(
                    "sale_recorded",
                    lang,
                    code=sale.public_code,
                    total=format_xaf(sale.total_amount),
                ),
                [
                    {
                        "id": f"receipt:{sale.public_code}",
                        "title": t("btn_receipt", lang)[:20],
                    },
                    {"id": "menu_sales", "title": t("btn_sales", lang)[:20]},
                    {"id": "main_menu", "title": t("btn_menu", lang)[:20]},
                ],
            )
            return {
                "ok": True,
                "action": "sale_recorded",
                "sale_code": sale.public_code,
                "total": str(sale.total_amount),
            }

    # Free-form product text only when it looks intentional.
    if any(
        token in lowered
        for token in ("produit", "product", "ajouter", "j'ai", "stock", "fcfa", "xaf")
    ) and not lowered.startswith(("vente ", "vendre ", "sale ", "sell ")):
        return _start_product_draft(db, adapter, conversation, from_number, content)

    _send_text(db, adapter, conversation, from_number, t("fallback", lang))
    _send_main_menu(db, adapter, store, conversation, from_number)
    return {"ok": True, "action": "fallback"}
