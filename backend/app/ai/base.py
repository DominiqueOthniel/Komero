from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Pluggable AI provider that always returns structured data."""

    @abstractmethod
    def extract_product(self, text: str, language: str = "fr") -> dict[str, Any]:
        raise NotImplementedError
