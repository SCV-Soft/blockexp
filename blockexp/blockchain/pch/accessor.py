from ..btc.accessor import BitcoinDaemonAccessor
from ..btc.types import BtcTransaction, BtcBlock


class PchDaemonAccessor(BitcoinDaemonAccessor):
    def _convert_raw_transaction(self, transaction: dict) -> BtcTransaction:
        transaction['hash'] = transaction['txid']
        transaction['vsize'] = transaction['size']
        transaction['weight'] = -1
        return BtcTransaction(**transaction)

    def _convert_raw_block(self, block: dict) -> BtcBlock:
        del block['acc_checkpoint']
        del block['modifier']
        del block['moneysupply']
        del block['zPCHsupply']
        block['strippedsize'] = block['size']
        block['weight'] = -1
        block['versionHex'] = '-'
        block['nTx'] = len(block['tx'])

        return BtcBlock(**block)