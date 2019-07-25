__all__ = ["value2amount"]


def value2amount(value: float) -> int:
    return round(value * 1e8)
