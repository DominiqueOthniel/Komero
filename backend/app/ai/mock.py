import re
from typing import Any

from app.ai.base import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic extractor for local development without API keys."""

    def extract_product(self, text: str, language: str = "fr") -> dict[str, Any]:
        price_match = re.search(
            r"(\d[\d\s.,]{2,})\s*(?:fcfa|xaf|f)?",
            text,
            flags=re.IGNORECASE,
        )
        stock_match = re.search(
            r"(\d+)\s*(?:pieces?|pcs?|en stock|available)?",
            text,
            flags=re.IGNORECASE,
        )
        size_matches = re.findall(
            r"(?:taille|size)\s*(\d+)",
            text,
            flags=re.IGNORECASE,
        )

        price = None
        if price_match:
            raw = price_match.group(1).replace(" ", "").replace(",", "")
            try:
                price = float(raw)
            except ValueError:
                price = None

        name = text.strip().split(",")[0].strip()
        name = re.sub(r"\d[\d\s.,]*\s*(fcfa|xaf|f)?", "", name, flags=re.I).strip()
        name = name or None

        variants = [
            {"name": "size", "value": size, "stock": None} for size in size_matches
        ]

        missing: list[str] = []
        if not name:
            missing.append("name")
        if price is None:
            missing.append("price")

        return {
            "name": name,
            "description": None,
            "price": price,
            "currency": "XAF",
            "stock": int(stock_match.group(1)) if stock_match else None,
            "variants": variants,
            "missing_fields": missing,
            "confidence": 0.55 if missing else 0.8,
        }
