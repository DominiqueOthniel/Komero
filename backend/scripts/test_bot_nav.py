#!/usr/bin/env python3
"""Smoke tests for structured WhatsApp bot navigation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.product import Product
from app.models.store import Store
from app.services.conversation_engine import handle_incoming_message
from app.whatsapp.mock import MockWhatsAppAdapter


def main() -> None:
    db = SessionLocal()
    adapter = MockWhatsAppAdapter()
    try:
        store = db.scalar(select(Store).order_by(Store.created_at.asc()))
        if not store:
            raise SystemExit("No store. Run seed first.")

        phone = f"2376700{__import__('secrets').randbelow(10**5):05d}"
        adapter.sent.clear()
        r = handle_incoming_message(
            db, adapter, store=store, from_number=phone, text="bonjour"
        )
        assert r["action"] == "choose_language", r

        welcome = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Francais",
            button_id="lang_fr",
        )
        assert welcome["action"] == "welcome", welcome
        assert welcome.get("lang") == "fr"
        assert any(m.get("type") == "buttons" for m in adapter.sent), adapter.sent
        print("Language + main menu OK")

        products = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="menu_products",
        )
        assert products["action"] == "products_menu", products

        add = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="add_product",
        )
        assert add["action"] == "add_product_prompt", add

        draft = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Pagne bleu 8000 FCFA, 3 pieces",
        )
        assert draft["action"] == "product_confirm_prompt", draft
        pub = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Confirmer",
            button_id="product_confirm",
        )
        assert pub["action"] == "product_published", pub
        product_id = pub["product_id"]
        print("Add product via menu OK")

        handle_incoming_message(
            db, adapter, store=store, from_number=phone, text="menu"
        )
        handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="menu_products",
        )
        delete_prompt = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="delete_product",
        )
        assert delete_prompt["action"] == "delete_prompt", delete_prompt

        # Find index of the product we just created among listed products.
        listed = list(
            db.scalars(
                select(Product)
                .where(Product.store_id == store.id)
                .order_by(Product.created_at.desc())
                .limit(10)
            )
        )
        index = next(
            i for i, p in enumerate(listed, 1) if str(p.id) == product_id
        )
        confirm = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text=str(index),
        )
        assert confirm["action"] == "confirm_delete", confirm
        deleted = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="delete_yes",
        )
        assert deleted["action"] == "product_deleted", deleted
        assert db.get(Product, __import__("uuid").UUID(product_id)) is None
        print("Delete product OK")

        lang_switch = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="change_language",
        )
        assert lang_switch["action"] == "choose_language", lang_switch
        en = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id="lang_en",
        )
        assert en["action"] == "welcome" and en.get("lang") == "en", en
        print("Language switch OK")
        print("All bot nav checks passed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
