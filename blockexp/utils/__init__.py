from dataclasses import asdict
from typing import Any


def asrow(obj: Any) -> dict:
    data = asdict(obj)
    data.pop('_id')
    data.pop('chain')
    data.pop('network')
    return data