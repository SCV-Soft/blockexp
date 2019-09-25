from dataclasses import dataclass
from typing import Any

from ..btc.types.legacy import LegacyBtcTransaction, LegacyBtcBlock


class AbleTransaction(LegacyBtcTransaction):
    pass


@dataclass
class AbleBlock(LegacyBtcBlock):
    TRANSACTION_CLASS = AbleTransaction  # used in parse_tx
    zABLEsupply: Any = None
    modifierV2: Any = None
