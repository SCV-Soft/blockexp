from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from ..utils import check_schemas


class Direction(IntEnum):
    ASCENDING = 1
    DESCENDING = -1


@dataclass
class SteamingFindOptions:
    paging: str = None
    since: int = None
    sort: Any = None
    direction: Direction = None
    limit: int = None


check_schemas(globals())
