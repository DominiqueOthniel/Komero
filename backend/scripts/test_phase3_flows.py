#!/usr/bin/env python3
"""Smoke-test AI product confirmation and onboarding flows."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.ai.mock import MockAIProvider
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.store import Store, StoreStatus
from app.models.user import User
from app.services.conversation_engine import handle_incoming_message
from app.services.onboarding import find_or_create_merchant_store
from app.whatsapp.mock import MockWhatsAppAdapter


def main() -> None:
    ai = MockAIProvider().extract_product(
        "Nike Air Max 95 noire a 45000 FCFA, j'en ai 4 en taille 42 et 2 en taille 43."
    )
    assert ai["name"] and "Nike" in ai["name"], ai
    assert ai["price"] == 45000.0, ai
    assert ai["stock"] == 6, ai
    assert len(ai["variants"]) >= 2, ai
    print("AI extract OK")

    db = SessionLocal()
    adapter = MockWhatsAppAdapter()
    try:
        store = db.scalar(select(Store).order_by(Store.created_at.asc()))
        if not store:
            raise SystemExit("No store in DB. Run seed first.")

        phone = "237670099001"
        adapter.sent.clear()
        r1 = handle_incoming_message(
            db, adapter, store=store, from_number=phone, text="", button_id="add_product"
        )
        assert r1["action"] == "add_product_prompt", r1

        adapter.sent.clear()
        r2 = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Robe wax 15000 FCFA, 8 pieces",
        )
        assert r2["action"] == "product_confirm_prompt", r2
        assert any(m.get("type") == "buttons" for m in adapter.sent), adapter.sent

        adapter.sent.clear()
        r3 = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=phone,
            text="Confirm",
            button_id="product_confirm",
        )
        assert r3["action"] == "product_published", r3
        product = db.scalar(
            select(Product).where(
                Product.store_id == store.id, Product.name.ilike("%Robe wax%")
            )
        )
        assert product is not None, "product missing"
        print("Product publish OK:", product.name, product.price)

        merchant_phone = "237655500111"
        draft_store = find_or_create_merchant_store(db, merchant_phone)
        assert draft_store.status == StoreStatus.DRAFT
        adapter.sent.clear()
        o1 = handle_incoming_message(
            db,
            adapter,
            store=draft_store,
            from_number=merchant_phone,
            text="bonjour",
        )
        assert o1["action"] == "ask_store_name", o1
        adapter.sent.clear()
        o2 = handle_incoming_message(
            db,
            adapter,
            store=draft_store,
            from_number=merchant_phone,
            text="Boutique Soleil",
        )
        assert o2["action"] == "store_created", o2
        db.refresh(draft_store)
        assert draft_store.status == StoreStatus.ACTIVE
        assert draft_store.name == "Boutique Soleil"
        print("Onboarding OK:", draft_store.slug)

        # cleanup draft merchant created by this script
        owner = db.get(User, draft_store.owner_id)
        db.delete(draft_store)
        if owner and owner.email.startswith("wa."):
            db.delete(owner)
        db.commit()
        print("All Phase 3 smoke checks passed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
