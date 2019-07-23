from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Type, Any

from starlette_typed.marshmallow import Schema, build_schema
from ..utils import check_schemas

SCHEMAS = {}


def get_schema(cls: Type, *, many: bool) -> Schema:
    schema = SCHEMAS.get((cls, many))
    if schema is None:
        schema = SCHEMAS[(cls, many)] = build_schema(cls, many=many)

    return schema


@dataclass
class Block:
    chain: str
    network: str
    confirmations: Optional[int]
    height: int
    hash: str
    version: int
    merkleRoot: str
    time: datetime
    timeNormalized: datetime
    nonce: int
    previousBlockHash: str
    nextBlockHash: str
    transactionCount: int
    size: int
    bits: int
    reward: Optional[int] = None
    processed: Optional[bool] = None
    _id: str = None


@dataclass
class Coin:
    chain: str
    network: str
    mintTxid: str
    mintIndex: int
    mintHeight: int = -1
    coinbase: bool = False
    value: int = None
    script: str = None
    address: str = None
    addresses: List[str] = field(default_factory=list)
    spentTxid: str = None
    spentHeight: int = -1
    confirmations: Optional[int] = 0
    wallets: List[str] = field(default_factory=list)
    _id: str = None


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
    address: str = None
    addresses: List[str] = field(default_factory=list)
    wallets: List[str] = field(default_factory=list)
    _id: str = None


@dataclass
class TransactionId:
    txid: str


@dataclass
class Balance:
    confirmed: int = 0
    unconfirmed: int = 0
    balance: int = 0


@dataclass
class EstimateFee:
    feerate: float
    blocks: int


@dataclass
class Wallet:
    chain: str
    network: str
    name: str
    pubKey: str
    path: Optional[str] = None
    singleAddress: Optional[bool] = None
    _id: str = None


@dataclass
class WalletAddress:
    chain: str
    network: str
    wallet: str
    address: str
    processed: bool = False
    _id: str = None


@dataclass
class WalletCheckResult:
    lastAddress: Optional[str]
    sum: int


@dataclass
class DailyTransactions:
    chain: str
    network: str
    results: List[Any]


check_schemas(globals())
