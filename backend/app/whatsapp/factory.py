from app.core.config import get_settings
from app.whatsapp.base import WhatsAppAdapter
from app.whatsapp.meta import MetaWhatsAppAdapter
from app.whatsapp.mock import MockWhatsAppAdapter


def get_whatsapp_adapter() -> WhatsAppAdapter:
    settings = get_settings()
    if settings.whatsapp_adapter == "meta" and settings.whatsapp_access_token:
        return MetaWhatsAppAdapter()
    return MockWhatsAppAdapter()
