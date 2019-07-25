from dataclasses import dataclass
from typing import Any

from ..btc.legacy import LegacyBtcTransaction, LegacyBtcBlock


class JackTransaction(LegacyBtcTransaction):
    pass


@dataclass
class JackBlock(LegacyBtcBlock):
    TRANSACTION_CLASS = JackTransaction  # used in parse_tx
    zJACKsupply: Any = None
