from .types import JackBlock, JackTransaction
from ..btc.accessor import BitcoinDaemonAccessor


class JackDaemonAccessor(BitcoinDaemonAccessor):
    def _convert_raw_transaction(self, transaction: dict) -> JackTransaction:
        JackTransaction.fix_tx(transaction)
        return JackTransaction(**transaction)

    def _convert_raw_block(self, block: dict) -> JackBlock:
        JackBlock.fix_block(block)
        return JackBlock(**block)
