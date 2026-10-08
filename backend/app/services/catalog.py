from app.core.config import get_settings
from app.models.store import Store


def shop_catalog_url(store: Store) -> str:
    settings = get_settings()
    return f"{settings.frontend_url.rstrip('/')}/shop/{store.slug}"


def product_page_url(store: Store, product_id: str) -> str:
    settings = get_settings()
    return (
        f"{settings.frontend_url.rstrip('/')}/shop/{store.slug}/product/{product_id}"
    )


def public_media_url(kind: str, filename: str) -> str:
    settings = get_settings()
    base = settings.public_api_url.rstrip("/") or "https://komero-production.up.railway.app"
    prefix = settings.api_prefix.rstrip("/")
    return f"{base}{prefix}/public/media/{kind}/{filename}"
