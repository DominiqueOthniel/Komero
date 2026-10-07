from decimal import Decimal


def format_xaf(amount: Decimal | int | float | str) -> str:
    value = Decimal(str(amount))
    whole = int(value.quantize(Decimal("1")))
    formatted = f"{whole:,}".replace(",", " ")
    return f"{formatted} F"
