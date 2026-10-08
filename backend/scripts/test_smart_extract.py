#!/usr/bin/env python3
"""Unit checks for smart product extraction."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.mock import MockAIProvider


def main() -> None:
    ai = MockAIProvider()

    ford = ai.extract_product("2022 Ford 1,5M", language="fr")
    assert ford["name"] and "Ford" in ford["name"], ford
    assert "2022" in ford["name"], ford
    assert ford["price"] == 1_500_000.0, ford
    assert ford["stock"] == 1, ford
    assert not ford["missing_fields"], ford
    print("Ford 1,5M OK:", ford["name"], ford["price"], ford["stock"])

    ford_dot = ai.extract_product_from_image(
        image_path="/tmp/fake.jpg", caption="2022 Ford 1.5M", language="en"
    )
    assert ford_dot["price"] == 1_500_000.0, ford_dot
    print("Image caption 1.5M OK")

    phone = ai.extract_product("iPhone 13 180k", language="fr")
    assert phone["price"] == 180_000.0, phone
    assert phone["name"] and "iPhone" in phone["name"], phone
    print("180k OK:", phone["name"], phone["price"])

    robe = ai.extract_product("Robe wax 15000 FCFA, 8 pieces", language="fr")
    assert robe["price"] == 15000.0, robe
    assert robe["stock"] == 8, robe
    print("Classic FCFA OK:", robe["name"], robe["price"], robe["stock"])

    nike = ai.extract_product(
        "Nike Air Max 95 noire a 45000 FCFA, j'en ai 4 en taille 42 et 2 en taille 43."
    )
    assert nike["price"] == 45000.0, nike
    assert nike["stock"] == 6, nike
    assert len(nike["variants"]) >= 2, nike
    print("Nike variants OK")

    # Year alone must not become the price.
    year_only = ai.extract_product("Toyota Corolla 2019", language="fr")
    assert year_only["price"] is None or year_only["price"] != 2019.0, year_only
    assert "price" in year_only["missing_fields"], year_only
    print("Year not price OK")

    print("All smart extract checks passed")


if __name__ == "__main__":
    main()
