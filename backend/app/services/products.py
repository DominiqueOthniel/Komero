import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Category, Product, ProductImage, ProductVariant
from app.schemas.product import CategoryCreate, ProductCreate, ProductUpdate
from app.services.slug import slugify


def list_products(db: Session, store_id: uuid.UUID) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .where(Product.store_id == store_id)
            .options(
                selectinload(Product.images),
                selectinload(Product.variants),
            )
            .order_by(Product.created_at.desc())
        )
    )


def get_product(db: Session, store_id: uuid.UUID, product_id: uuid.UUID) -> Product | None:
    return db.scalar(
        select(Product)
        .where(Product.id == product_id, Product.store_id == store_id)
        .options(
            selectinload(Product.images),
            selectinload(Product.variants),
        )
    )


def create_product(db: Session, store_id: uuid.UUID, payload: ProductCreate) -> Product:
    product = Product(
        store_id=store_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        compare_price=payload.compare_price,
        stock_quantity=payload.stock_quantity,
        sku=payload.sku,
        category_id=payload.category_id,
        status=payload.status,
    )
    db.add(product)
    db.flush()

    for image in payload.images:
        db.add(
            ProductImage(
                product_id=product.id,
                image_url=image.image_url,
                position=image.position,
            )
        )
    for variant in payload.variants:
        db.add(
            ProductVariant(
                product_id=product.id,
                name=variant.name,
                value=variant.value,
                stock_quantity=variant.stock_quantity,
                price=variant.price,
            )
        )

    db.commit()
    return get_product(db, store_id, product.id)  # type: ignore[return-value]


def update_product(
    db: Session, product: Product, payload: ProductUpdate
) -> Product:
    data = payload.model_dump(exclude_unset=True, exclude={"images", "variants"})
    for key, value in data.items():
        setattr(product, key, value)

    if payload.images is not None:
        product.images.clear()
        db.flush()
        for image in payload.images:
            db.add(
                ProductImage(
                    product_id=product.id,
                    image_url=image.image_url,
                    position=image.position,
                )
            )

    if payload.variants is not None:
        product.variants.clear()
        db.flush()
        for variant in payload.variants:
            db.add(
                ProductVariant(
                    product_id=product.id,
                    name=variant.name,
                    value=variant.value,
                    stock_quantity=variant.stock_quantity,
                    price=variant.price,
                )
            )

    db.commit()
    return get_product(db, product.store_id, product.id)  # type: ignore[return-value]


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()


def create_category(db: Session, store_id: uuid.UUID, payload: CategoryCreate) -> Category:
    base = slugify(payload.name)
    slug = base
    index = 2
    while db.scalar(
        select(Category.id).where(Category.store_id == store_id, Category.slug == slug)
    ):
        slug = f"{base}-{index}"
        index += 1

    category = Category(store_id=store_id, name=payload.name, slug=slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
