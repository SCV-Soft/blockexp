from dataclasses import dataclass
from typing import List, Optional

from starlette_typed.marshmallow import schema


@dataclass
class Block:
    _id: str
    chain: str
    confirmations: Optional[int]
    network: str
    height: int
    hash: str
    version: int
    merkleRoot: str
    time: str  # Date
    timeNormalized: str  # Date
    nonce: int
    previousBlockHash: str
    nextBlockHash: str
    transactionCount: int
    size: int
    bits: int
    reward: int
    processed: Optional[bool] = None


BlockSchema = schema(Block)


@dataclass
class Coin:
    _id: str
    network: str
    chain: str
    mintTxid: str
    mintIndex: int
    mintHeight: int
    coinbase: bool
    value: int
    address: str
    script: str
    spentTxid: str
    spentHeight: int
    confirmations: Optional[int]


class CoinListing:
    inputs: List[Coin]
    outputs: List[Coin]


class Transaction:
    _id: str
    txid: str
    chain: str
    network: str
    blockHeight: int
    blockHash: str
    blockTime: str
    blockTimeNormalized: str
    coinbase: bool
    fee: int
    size: int
    locktime: int
    inputCount: int
    outputCount: int
    value: int
