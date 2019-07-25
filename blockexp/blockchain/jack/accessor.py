from .types import JackBlock, JackTransaction
from ..btc.accessor import BitcoinDaemonAccessor


class JackDaemonAccessor(BitcoinDaemonAccessor):
    def _convert_raw_transaction(self, transaction: dict) -> JackTransaction:
        return JackTransaction.load(transaction)

    def _convert_raw_block(self, block: dict) -> JackBlock:
        return JackBlock.load(block)
