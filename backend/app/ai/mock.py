import re
from typing import Any

from app.ai.base import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic extractor for local development without API keys."""

    def extract_product(self, text: str, language: str = "fr") -> dict[str, Any]:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return {
                "name": None,
                "description": None,
                "price": None,
                "currency": "XAF",
                "stock": None,
                "variants": [],
                "missing_fields": ["name", "price"],
                "confidence": 0.1,
            }

        price_match = re.search(
            r"(?:a|à|@|prix)?\s*(\d(?:[\d\s]{0,12}\d)?(?:[.,]\d+)?)\s*(?:fcfa|xaf|f\.?cfa|f)\b",
            cleaned,
            flags=re.IGNORECASE,
        )
        if not price_match:
            price_match = re.search(
                r"\b(\d(?:[\d\s]{2,12}\d)?(?:[.,]\d+)?)\b",
                cleaned,
            )

        price = None
        if price_match:
            raw = price_match.group(1).replace(" ", "").replace(",", ".")
            try:
                price = float(raw)
            except ValueError:
                price = None

        size_matches = re.findall(
            r"(?:taille|size)\s*([A-Za-z0-9]+)",
            cleaned,
            flags=re.IGNORECASE,
        )

        stock = None
        qty_pairs = re.findall(
            r"(\d+)\s*(?:en\s+)?(?:taille|size)\s*[A-Za-z0-9]+",
            cleaned,
            flags=re.IGNORECASE,
        )
        if qty_pairs:
            stock = sum(int(q) for q in qty_pairs)
        if stock is None:
            stock_match = re.search(
                r"(?:j'?en ai|stock|disponible|available)\s*(\d+)",
                cleaned,
                flags=re.IGNORECASE,
            )
            if stock_match:
                stock = int(stock_match.group(1))
        if stock is None:
            stock_match = re.search(
                r"(\d+)\s*(?:pieces?|pcs?)\b",
                cleaned,
                flags=re.IGNORECASE,
            )
            if stock_match:
                stock = int(stock_match.group(1))

        name_source = cleaned
        if price_match:
            name_source = cleaned[: price_match.start()] + cleaned[price_match.end() :]
        name_source = re.split(r"[,.]", name_source, maxsplit=1)[0]
        name_source = re.sub(
            r"\b(?:j'?en ai|stock|disponible|available|pieces?|pcs?)\b.*$",
            "",
            name_source,
            flags=re.IGNORECASE,
        )
        name_source = re.sub(
            r"\b(?:taille|size)\s*[A-Za-z0-9]+\b",
            "",
            name_source,
            flags=re.IGNORECASE,
        )
        name_source = re.sub(r"\b\d+\b", "", name_source)
        name = " ".join(name_source.split()).strip(" -:")
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
            "description": cleaned if name else None,
            "price": price,
            "currency": "XAF",
            "stock": stock,
            "variants": variants,
            "missing_fields": missing,
            "confidence": 0.55 if missing else 0.85,
        }
