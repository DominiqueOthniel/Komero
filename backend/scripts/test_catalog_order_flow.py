#!/usr/bin/env python3
"""Smoke test: catalog Commander → merchant invoice/payment buttons."""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.order import Order, PaymentStatus
from app.models.product import Product, ProductStatus
from app.models.store import Store
from app.services.conversation_engine import handle_incoming_message
from app.services.orders import create_catalog_order, merchant_notify_number, order_ref
from app.services.conversation_engine import notify_merchant_catalog_order
from app.whatsapp.mock import MockWhatsAppAdapter


def main() -> None:
    db = SessionLocal()
    adapter = MockWhatsAppAdapter()
    try:
        store = db.scalar(select(Store).order_by(Store.created_at.asc()))
        if not store:
            raise SystemExit("No store. Run seed first.")
        product = db.scalar(
            select(Product).where(
                Product.store_id == store.id,
                Product.status == ProductStatus.PUBLISHED,
            )
        )
        if not product:
            raise SystemExit("No published product.")

        merchant = merchant_notify_number(db, store)
        assert merchant, "merchant notify number missing"

        # 1) Web Commander creates order + merchant prompt
        adapter.sent.clear()
        order = create_catalog_order(
            db,
            store,
            product=product,
            quantity=1,
            notes="source:catalog_web",
        )
        notify_to = notify_merchant_catalog_order(
            db, adapter, store, order, customer_label="Catalogue web"
        )
        assert notify_to == merchant, (notify_to, merchant)
        assert any(m.get("type") == "buttons" for m in adapter.sent), adapter.sent
        button_ids = [
            b["id"]
            for m in adapter.sent
            if m.get("type") == "buttons"
            for b in m.get("buttons") or []
        ]
        assert any(bid.startswith("order_paid:") for bid in button_ids), button_ids
        assert any(bid.startswith("order_receipt:") for bid in button_ids), button_ids
        print("Merchant notify OK", order_ref(order))

        # 2) Merchant marks paid
        adapter.sent.clear()
        paid = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=merchant,
            text="Valider paye",
            button_id=f"order_paid:{order.id}",
        )
        assert paid["action"] == "order_paid", paid
        db.refresh(order)
        fresh = db.get(Order, order.id)
        assert fresh and fresh.payment_status == PaymentStatus.PAID
        print("Mark paid OK")

        # 3) Merchant starts receipt
        adapter.sent.clear()
        receipt = handle_incoming_message(
            db,
            adapter,
            store=store,
            from_number=merchant,
            text="Faire le recu",
            button_id=f"order_receipt:{order.id}",
        )
        assert receipt["action"] == "ask_receipt_name", receipt
        print("Receipt prompt OK")

        # 4) Customer WhatsApp order message (new product path / structured)
        customer = f"2376709{secrets.randbelow(10**5):05d}"
        adapter.sent.clear()
        text = (
            "Bonjour, je voudrais commander :\n\n"
            f"{product.name}\n"
            "Quantite : 1\n"
            f"Prix : {int(product.price)} F\n\n"
            f"Boutique : {store.name}\n\n"
            "KOMERO_ORDER\n"
            f"store:{store.slug}\n"
            f"product:{product.id}\n"
            "qty:1\n"
            f"price:{product.price}"
        )
        inbound = handle_incoming_message(
            db, adapter, store=store, from_number=customer, text=text
        )
        assert inbound["action"] == "catalog_order_received", inbound
        assert inbound.get("customer_ack") is True
        print("Customer inbound order OK", inbound.get("order_ref"))

        print("Catalog order flow OK")
    finally:
        db.close()


if __name__ == "__main__":
    main()
