#!/usr/bin/env python3
"""Smoke tests for catalog links, image products, and PDF receipts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.product import Product
from app.models.store import Store
from app.services.catalog import shop_catalog_url
from app.services.conversation_engine import handle_incoming_message
from app.whatsapp.mock import MockWhatsAppAdapter


def main() -> None:
    db = SessionLocal()
    adapter = MockWhatsAppAdapter()
    try:
        store = db.scalar(select(Store).order_by(Store.created_at.asc()))
        if not store:
            raise SystemExit("No store. Run seed first.")

        phone = "237670088221"
        adapter.sent.clear()
        r = handle_incoming_message(
            db, adapter, store=store, from_number=phone, text="bonjour"
        )
        assert r["action"] == "welcome", r
        catalog = handle_incoming_message(
            db, adapter, store=store, from_number=phone, text="", button_id="view_catalog"
        )
        assert catalog["action"] == "catalog_link", catalog
        assert shop_catalog_url(store) in (catalog.get("url") or "")
        assert any(m.get("type") == "cta_url" for m in adapter.sent), adapter.sent
        print("Catalog OK:", catalog["url"])

        adapter.sent.clear()
        img = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Sac cuir 25000 FCFA",
            media_id="img-test-1",
            media_kind="image",
            mime_type="image/jpeg",
        )
        assert img["action"] == "product_confirm_prompt", img
        pub = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Confirm",
            button_id="product_confirm",
        )
        assert pub["action"] == "product_published", pub
        product = db.get(Product, __import__("uuid").UUID(pub["product_id"]))
        assert product is not None
        assert product.images, "expected product image"
        print("Image product OK:", product.name, product.images[0].image_url)

        adapter.sent.clear()
        voice = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number="237670088222",
            text="",
            media_id="audio-test-1",
            media_kind="audio",
            mime_type="audio/ogg",
        )
        assert voice["action"] == "voice_received_pending_text", voice
        print("Voice handling OK")

        adapter.sent.clear()
        sale = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="vente Sac cuir 25000",
        )
        assert sale["action"] == "sale_recorded", sale
        code = sale["sale_code"]
        ask = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="",
            button_id=f"receipt:{code}",
        )
        assert ask["action"] == "ask_receipt_name", ask
        receipt = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="No name",
            button_id=f"receipt_noname:{code}",
        )
        assert receipt["action"] == "receipt_sent", receipt
        assert any(m.get("type") == "document" for m in adapter.sent), adapter.sent
        print("PDF receipt OK")
        print("All catalog/media/receipt checks passed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
