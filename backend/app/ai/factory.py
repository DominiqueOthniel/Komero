from app.ai.base import AIProvider
from app.ai.mock import MockAIProvider
from app.core.config import get_settings


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider == "mock":
        return MockAIProvider()
    # Future: openai, anthropic, etc.
    return MockAIProvider()
