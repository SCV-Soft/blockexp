from .types import PchBlock, PchTransaction
from ..btc.accessor import BtcDaemonAccessor


class PchDaemonAccessor(BtcDaemonAccessor):
    def _convert_raw_transaction(self, transaction: dict) -> PchTransaction:
        return PchTransaction.load(transaction)

    def _convert_raw_block(self, block: dict) -> PchBlock:
        return PchBlock.load(block)
