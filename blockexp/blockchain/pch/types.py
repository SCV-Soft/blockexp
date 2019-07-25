from dataclasses import dataclass
from typing import Any

from ..btc.types import BtcBlock, BtcTransaction


@dataclass
class PchBlock(BtcBlock):
    acc_checkpoint: Any = None
    modifier: Any = None
    moneysupply: Any = None
    zPCHsupply: Any = None

    @classmethod
    def fix_block(cls, raw_block):
        raw_block.setdefault('strippedsize', raw_block['size'])
        raw_block.setdefault('weight', -1)
        raw_block.setdefault('versionHex', '')
        raw_block.setdefault('nTx', len(raw_block['tx']))

    @classmethod
    def parse_tx(cls, raw_tx):
        PchTransaction.fix_tx(raw_tx)
        return PchTransaction(**raw_tx)


@dataclass
class PchTransaction(BtcTransaction):
    @classmethod
    def fix_tx(cls, raw_tx):
        raw_tx.setdefault('hash', raw_tx['txid'])
        raw_tx.setdefault('vsize', raw_tx['size'])
        raw_tx.setdefault('weight', -1)
