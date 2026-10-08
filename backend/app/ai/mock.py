import re
from typing import Any

from app.ai.base import AIProvider

YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
COMPACT_PRICE_RE = re.compile(
    r"(?<![\w.])(?P<num>\d+(?:[.,]\d+)?)\s*(?P<suffix>[kKmM])\b",
)
CURRENCY_PRICE_RE = re.compile(
    r"(?:(?:a|à|@|prix)\s*)?(?P<num>\d(?:[\d\s]{0,14}\d)?(?:[.,]\d+)?)\s*"
    r"(?:fcfa|xaf|f\.?cfa|f)\b",
    re.IGNORECASE,
)
PLAIN_PRICE_RE = re.compile(
    r"(?<![\w.])(?P<num>\d(?:[\d\s]{2,14}\d)|(?:\d{4,}))(?:[.,]\d+)?(?![\w.])",
)
STOCK_EXPLICIT_RE = re.compile(
    r"(?:j'?en ai|stock|disponible|available|qty|quantite|quantité)\s*(\d+)",
    re.IGNORECASE,
)
STOCK_PIECES_RE = re.compile(r"(\d+)\s*(?:pieces?|pcs?)\b", re.IGNORECASE)
SIZE_RE = re.compile(r"(?:taille|size)\s*([A-Za-z0-9]+)", re.IGNORECASE)
SIZE_QTY_RE = re.compile(
    r"(\d+)\s*(?:en\s+)?(?:taille|size)\s*[A-Za-z0-9]+",
    re.IGNORECASE,
)


def _parse_number(raw: str) -> float | None:
    text = raw.strip().replace(" ", "")
    if not text:
        return None
    # European decimal: 1,5 -> 1.5 ; thousands: 1.500.000 or 1,500,000
    if text.count(",") == 1 and text.count(".") == 0:
        text = text.replace(",", ".")
    elif text.count(".") > 1 and "," not in text:
        text = text.replace(".", "")
    elif text.count(",") > 1 and "." not in text:
        text = text.replace(",", "")
    elif text.count(",") == 1 and text.count(".") == 1:
        # 1.500,50 or 1,500.50
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _is_year(value: float) -> bool:
    return 1900 <= value <= 2100 and float(value).is_integer()


def _extract_price(cleaned: str) -> tuple[float | None, re.Match[str] | None]:
    """Pick the best price candidate; prefer compact M/K and currency-tagged amounts."""
    candidates: list[tuple[float, int, re.Match[str]]] = []

    for match in COMPACT_PRICE_RE.finditer(cleaned):
        num = _parse_number(match.group("num"))
        if num is None:
            continue
        suffix = match.group("suffix").lower()
        multiplier = 1_000_000 if suffix == "m" else 1_000
        price = num * multiplier
        # Higher score for compact African shorthand.
        candidates.append((price, 100, match))

    for match in CURRENCY_PRICE_RE.finditer(cleaned):
        num = _parse_number(match.group("num"))
        if num is None:
            continue
        candidates.append((num, 90, match))

    for match in PLAIN_PRICE_RE.finditer(cleaned):
        num = _parse_number(match.group("num"))
        if num is None or _is_year(num):
            continue
        # Plain numbers need to look like money (at least 4 digits / >= 1000).
        if num < 1000:
            continue
        candidates.append((num, 40, match))

    if not candidates:
        return None, None

    # Prefer higher score, then larger absolute value (vehicle prices etc.).
    candidates.sort(key=lambda item: (item[1], item[0]), reverse=True)
    price, _score, match = candidates[0]
    return price, match


def _extract_stock(cleaned: str) -> int | None:
    qty_pairs = SIZE_QTY_RE.findall(cleaned)
    if qty_pairs:
        return sum(int(q) for q in qty_pairs)
    stock_match = STOCK_EXPLICIT_RE.search(cleaned)
    if stock_match:
        return int(stock_match.group(1))
    stock_match = STOCK_PIECES_RE.search(cleaned)
    if stock_match:
        return int(stock_match.group(1))
    return None


def _extract_name(cleaned: str, price_match: re.Match[str] | None) -> str | None:
    name_source = cleaned
    if price_match:
        name_source = cleaned[: price_match.start()] + " " + cleaned[price_match.end() :]

    # Drop trailing stock / availability clauses, keep years in the title.
    name_source = re.sub(
        r",?\s*\d+\s*(?:pieces?|pcs?)\b.*$",
        " ",
        name_source,
        flags=re.IGNORECASE,
    )
    name_source = re.split(
        r"\b(?:j'?en ai|stock|disponible|available)\b",
        name_source,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    name_source = SIZE_RE.sub("", name_source)
    name_source = re.sub(
        r"\b(?:a|à|@|prix|fcfa|xaf|f\.?cfa)\b",
        " ",
        name_source,
        flags=re.IGNORECASE,
    )
    name_source = re.sub(r"[,:;|/]+", " ", name_source)
    name = " ".join(name_source.split()).strip(" -.")
    return name or None


def _guess_defaults(name: str | None, price: float | None, stock: int | None) -> int | None:
    """Dynamic defaults: single unique items (vehicles, phones) default stock 1."""
    if stock is not None or not name:
        return stock
    lowered = name.lower()
    unique_tokens = (
        "ford",
        "toyota",
        "hyundai",
        "mercedes",
        "bmw",
        "honda",
        "nissan",
        "voiture",
        "camion",
        "moto",
        "iphone",
        "samsung",
        "macbook",
        "ordinateur",
        "maison",
        "terrain",
        "appartement",
    )
    if any(token in lowered for token in unique_tokens):
        return 1
    if price is not None and price >= 500_000:
        return 1
    return stock


class MockAIProvider(AIProvider):
    """Smart deterministic extractor for merchant product messages."""

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
                "notes": [],
            }

        price, price_match = _extract_price(cleaned)
        stock = _extract_stock(cleaned)
        name = _extract_name(cleaned, price_match)
        stock = _guess_defaults(name, price, stock)

        size_matches = SIZE_RE.findall(cleaned)
        variants = [
            {"name": "size", "value": size, "stock": None} for size in size_matches
        ]

        year = None
        year_match = YEAR_RE.search(cleaned)
        if year_match:
            year = year_match.group(1)
            if name and year not in name:
                # Keep model year visible in the title when present.
                if not name.lower().startswith(year):
                    name = f"{year} {name}".strip()

        missing: list[str] = []
        notes: list[str] = []
        if not name:
            missing.append("name")
        if price is None:
            missing.append("price")
            notes.append(
                "Indiquez le prix clairement, ex: 15000 FCFA ou 1,5M."
                if language.startswith("fr")
                else "Add a clear price, e.g. 15000 FCFA or 1.5M."
            )
        if stock is None:
            notes.append(
                "Stock non precise : vous pourrez le completer apres publication."
                if language.startswith("fr")
                else "Stock not set: you can complete it after publishing."
            )

        confidence = 0.9
        if missing:
            confidence = 0.45
        elif notes:
            confidence = 0.75
        if price is not None and price_match and COMPACT_PRICE_RE.search(price_match.group(0) or ""):
            confidence = min(0.95, confidence + 0.05)

        return {
            "name": name,
            "description": cleaned if name else None,
            "price": price,
            "currency": "XAF",
            "stock": stock,
            "variants": variants,
            "missing_fields": missing,
            "confidence": confidence,
            "notes": notes,
            "year": year,
        }
