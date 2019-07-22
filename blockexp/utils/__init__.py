from dataclasses import asdict, is_dataclass
from typing import Any

from starlette_typed.marshmallow import check_schema


def asrow(obj: Any) -> dict:
    data = asdict(obj)
    data.pop('_id')
    data.pop('chain')
    data.pop('network')
    return data


def check_schemas(ctx: dict):
    for cls in list(ctx.values()):
        if is_dataclass(cls):
            check_schema(cls)
