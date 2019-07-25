from .types import PchBlock, PchTransaction
from ..btc.accessor import BitcoinDaemonAccessor


class PchDaemonAccessor(BitcoinDaemonAccessor):
    def _convert_raw_transaction(self, transaction: dict) -> PchTransaction:
        PchTransaction.fix_tx(transaction)
        return PchTransaction(**transaction)

    def _convert_raw_block(self, block: dict) -> PchBlock:
        PchBlock.fix_block(block)
        return PchBlock(**block)
