"""Seed a demo merchant, store, and products for local development."""

from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.product import Category, Product, ProductImage, ProductStatus
from app.models.store import Store, StoreStatus
from app.models.user import User, UserRole
from app.services.slug import slugify
from sqlalchemy import select


def seed() -> None:
    db = SessionLocal()
    try:
        email = "merchant@komero.test"
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                name="Awa Merchant",
                email=email,
                password_hash=hash_password("password123"),
                phone="+237670000000",
                role=UserRole.MERCHANT,
            )
            db.add(user)
            db.flush()

        store = db.scalar(select(Store).where(Store.slug == "chez-awa"))
        if not store:
            store = Store(
                owner_id=user.id,
                name="Chez Awa",
                slug="chez-awa",
                description="Mode et accessoires depuis WhatsApp.",
                currency="XAF",
                phone="+237670000000",
                whatsapp_number="237670000000",
                primary_color="#0F6B5C",
                status=StoreStatus.ACTIVE,
            )
            db.add(store)
            db.flush()

        dresses = db.scalar(
            select(Category).where(
                Category.store_id == store.id, Category.slug == "dresses"
            )
        )
        if not dresses:
            dresses = Category(
                store_id=store.id, name="Dresses", slug=slugify("Dresses")
            )
            db.add(dresses)
            db.flush()

        existing = db.scalar(
            select(Product).where(
                Product.store_id == store.id, Product.name == "Wax dress"
            )
        )
        if not existing:
            product = Product(
                store_id=store.id,
                category_id=dresses.id,
                name="Wax dress",
                description="Robe wax, tailles 40 a 44.",
                price=Decimal("12000.00"),
                stock_quantity=3,
                status=ProductStatus.PUBLISHED,
            )
            db.add(product)
            db.flush()
            db.add(
                ProductImage(
                    product_id=product.id,
                    image_url="/images/product-wax.jpg",
                    position=0,
                )
            )

            bag = Product(
                store_id=store.id,
                name="Leather bag",
                description="Sac cuir pour le quotidien.",
                price=Decimal("5000.00"),
                stock_quantity=4,
                status=ProductStatus.PUBLISHED,
            )
            db.add(bag)
            db.flush()
            db.add(
                ProductImage(
                    product_id=bag.id,
                    image_url="/images/product-bag.jpg",
                    position=0,
                )
            )

        db.commit()
        print("Seed complete")
        print("Login: merchant@komero.test / password123")
        print("Shop: /shop/chez-awa")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
