from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Pluggable AI provider that always returns structured data."""

    @abstractmethod
    def extract_product(self, text: str, language: str = "fr") -> dict[str, Any]:
        raise NotImplementedError

    def extract_product_from_image(
        self,
        *,
        image_path: str,
        caption: str = "",
        language: str = "fr",
    ) -> dict[str, Any]:
        """Default image extraction uses caption text plus an image hint."""
        text = caption.strip() or "Produit photo"
        draft = self.extract_product(text, language=language)
        draft["source"] = "image"
        draft["image_path"] = image_path
        if not caption.strip():
            missing = list(draft.get("missing_fields") or [])
            for field in ("name", "price"):
                if field not in missing:
                    missing.append(field)
            draft["missing_fields"] = missing
            draft["confidence"] = min(float(draft.get("confidence") or 0.4), 0.45)
        return draft
