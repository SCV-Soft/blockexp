from dataclasses import dataclass
from typing import List, Optional

from starlette_typed.marshmallow import schema


@dataclass
class Block:
    _id: str
    chain: str
    network: str
    confirmations: Optional[int]
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


@dataclass
class Coin:
    _id: str
    chain: str
    network: str
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


@dataclass
class CoinListing:
    inputs: List[Coin]
    outputs: List[Coin]


@dataclass
class Authhead:
    chain: str
    network: str
    authbase: str
    identityOutputs: List[Coin]


@dataclass
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
    confirmations: Optional[int] = None


@dataclass
class TransactionId:
    txid: str


@dataclass
class AddressBalance:
    confirmed: int = 0
    unconfirmed: int = 0
    balance: int = 0


@dataclass
class EstimateFee:
    feerate: float
    blocks: int
