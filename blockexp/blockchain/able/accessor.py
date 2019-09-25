from .types import AbleBlock, AbleTransaction
from ..btc.accessor import BtcDaemonAccessor


class AbleDaemonAccessor(BtcDaemonAccessor):
    def _convert_raw_transaction(self, transaction: dict) -> AbleTransaction:
        return AbleTransaction.load(transaction)

    def _convert_raw_block(self, block: dict) -> AbleBlock:
        return AbleBlock.load(block)
