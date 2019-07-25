from dataclasses import dataclass
from typing import Any

from ..btc.types.legacy import LegacyBtcTransaction, LegacyBtcBlock


class PchTransaction(LegacyBtcTransaction):
    pass


@dataclass
class PchBlock(LegacyBtcBlock):
    TRANSACTION_CLASS = PchTransaction  # used in parse_tx
    zPCHsupply: Any = None
