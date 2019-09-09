from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union

from hexbytes import HexBytes


def as_bytes(s: Union[str, bytes]) -> Optional[HexBytes]:
    return HexBytes(s) if s else None


def as_int(s: Union[str, int]) -> int:
    if isinstance(s, int):
        return s

    return int(s, 16)


@dataclass(init=False)
class EthBlock:
    _raw: dict = field(repr=False)
    number: int  # the block number. null when its pending block.
    hash: HexBytes  # 32 Bytes | hash of the block. null when its pending block.
    parentHash: HexBytes  # 32 Bytes | hash of the parent block.
    nonce: HexBytes  # 8 Bytes | hash of the generated proof-of-work. null when its pending block.
    sha3Uncles: HexBytes  # 32 Bytes | SHA3 of the uncles data in the block.
    logsBloom: HexBytes  # 256 Bytes | the bloom filter for the logs of the block. null when its pending block.
    transactionsRoot: HexBytes  # 32 Bytes | the root of the transaction trie of the block.
    stateRoot: HexBytes  # 32 Bytes | the root of the final state trie of the block.
    receiptsRoot: HexBytes  # 32 Bytes | the root of the receipts trie of the block.
    miner: HexBytes  # 20 Bytes | the address of the beneficiary to whom the mining rewards were given.
    difficulty: int  # integer of the difficulty for this block.
    totalDifficulty: int  # integer of the total difficulty of the chain until this block.
    extraData: HexBytes  # the "extra data" field of this block.
    size: int  # integer the size of this block in bytes.
    gasLimit: int  # the maximum gas allowed in this block.
    gasUsed: int  # the total used gas by all transactions in this block.
    timestamp: datetime  # the unix timestamp for when the block was collated.
    transactions: List[Union[EthTransaction, str, dict]]  # Array of transaction objects,
    # or 32 Bytes transaction hashes depending on the last given parameter.
    uncles: List[HexBytes]  # Array of uncle hashes.
    mixHash: str

    def __init__(self, **raw_block):
        self._raw = raw_block.copy()
        self.number = as_int(raw_block.pop('number'))
        self.hash = as_bytes(raw_block.pop('hash'))
        self.parentHash = as_bytes(raw_block.pop('parentHash'))
        self.nonce = as_bytes(raw_block.pop('nonce'))
        self.sha3Uncles = as_bytes(raw_block.pop('sha3Uncles'))
        self.logsBloom = as_bytes(raw_block.pop('logsBloom'))
        self.transactionsRoot = as_bytes(raw_block.pop('transactionsRoot'))
        self.stateRoot = as_bytes(raw_block.pop('stateRoot'))
        self.receiptsRoot = as_bytes(raw_block.pop('receiptsRoot'))
        self.miner = as_bytes(raw_block.pop('miner'))
        self.difficulty = as_int(raw_block.pop('difficulty'))
        self.totalDifficulty = as_int(raw_block.pop('totalDifficulty'))
        self.extraData = as_bytes(raw_block.pop('extraData'))
        self.size = as_int(raw_block.pop('size'))
        self.gasLimit = as_int(raw_block.pop('gasLimit'))
        self.gasUsed = as_int(raw_block.pop('gasUsed'))
        self.timestamp = datetime.utcfromtimestamp(as_int(raw_block.pop('timestamp')))
        self.transactions = raw_block.pop('transactions')
        self.uncles = raw_block.pop('uncles')
        self.mixHash = raw_block.pop('mixHash')
        assert not raw_block, list(raw_block.keys())

        if self.transactions and isinstance(self.transactions[0], dict):
            self.transactions = [self.parse_tx(item) for item in self.transactions]

    @classmethod
    def parse_tx(cls, raw_tx: dict):
        return EthTransaction.load(raw_tx)

    @classmethod
    def load(cls, raw_block: dict):
        cls.fix_block(raw_block)
        return cls(**raw_block)

    @classmethod
    def fix_block(self, raw_block: dict):
        pass


@dataclass(init=False)
class EthTransaction:
    _raw: dict = field(repr=False)
    blockHash: HexBytes  # 32 Bytes | hash of the block where this transaction was in. null when its pending.
    blockNumber: int  # block number where this transaction was in. null when its pending.
    from_: HexBytes  # 20 Bytes | address of the sender.
    gas: int  # gas provided by the sender.
    gasPrice: int  # gas price provided by the sender in Wei.
    hash: HexBytes  # 32 Bytes | hash of the transaction.
    input: HexBytes  # the data send along with the transaction.
    nonce: int  # the number of transactions made by the sender prior to this one.
    transactionIndex: int  # integer of the transaction's index position in the block. null when its pending.
    value: int  # value transferred in Wei.
    v: int  # ECDSA recovery id
    r: HexBytes  # 32 Bytes | ECDSA signature r
    s: HexBytes  # 32 Bytes | ECDSA signature s
    to: HexBytes = field(
        default=None)  # 20 Bytes | address of the receiver. null when its a contract creation transaction.

    def __init__(self, **raw_tx):
        self._raw = raw_tx.copy()
        self.blockHash = as_bytes(raw_tx.pop('blockHash'))
        self.blockNumber = as_int(raw_tx.pop('blockNumber'))
        self.from_ = as_bytes(raw_tx.pop('from'))
        self.gas = as_int(raw_tx.pop('gas'))
        self.gasPrice = as_int(raw_tx.pop('gasPrice'))
        self.hash = as_bytes(raw_tx.pop('hash'))
        self.input = as_bytes(raw_tx.pop('input'))
        self.nonce = as_int(raw_tx.pop('nonce'))
        self.transactionIndex = as_int(raw_tx.pop('transactionIndex'))
        self.value = as_int(raw_tx.pop('value'))
        self.v = as_int(raw_tx.pop('v'))
        self.r = as_bytes(raw_tx.pop('r'))
        self.s = as_bytes(raw_tx.pop('s'))
        self.to = as_bytes(raw_tx.pop('to'))

    @classmethod
    def fix_tx(cls, raw_tx: dict):
        pass

    @classmethod
    def load(cls, raw_tx: dict):
        cls.fix_tx(raw_tx)
        return cls(**raw_tx)
