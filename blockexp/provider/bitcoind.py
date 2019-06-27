from dataclasses import dataclass
from datetime import datetime
from typing import Union, Type, TypeVar, cast, Any, List, Tuple

import typing_inspect
from requests.auth import HTTPBasicAuth
from requests_async import Response

from blockexp.proxy.bitcoind import AsyncBitcoreDeamon
from starlette_typed.marshmallow import build_schema, Schema
from .base import Provider, ProviderType
from ..model import Block, Transaction

T = TypeVar('T')

SCHEMAS = {}


def get_schema(cls: Type, *, many: bool) -> Schema:
    schema = SCHEMAS.get((cls, many))
    if schema is None:
        schema = SCHEMAS[(cls, many)] = build_schema(cls, many=many)

    return schema


# TODO: valid dataclass?

@dataclass
class BtcVInCoinbase:
    coinbase: str
    sequence: int


@dataclass
class BtcVIn:
    txid: str
    vout: int
    scriptSig: dict
    sequence: int
    txinwitness: List[str] = None


@dataclass
class BtcVOut:
    value: float
    n: int
    scriptPubKey: dict


# noinspection SpellCheckingInspection
@dataclass
class BtcTransaction:
    txid: str
    hash: str
    version: int
    size: int
    vsize: int
    weight: int
    locktime: int
    vin: List[Union[dict, BtcVIn, BtcVInCoinbase]]
    vout: List[Union[dict, BtcVOut]]
    hex: str
    blockhash: str = None
    confirmations: int = None
    time: int = None
    blocktime: int = None

    def is_coinbase(self) -> bool:
        return isinstance(self.vin[0], BtcVInCoinbase) if self.vin else False

    def __post_init__(self):
        if self.vin and not isinstance(self.vin[0], (BtcVIn, BtcVInCoinbase)):
            item = self.vin[0]
            if 'coinbase' in item:
                assert len(self.vin) == 1
                self.vin = [BtcVInCoinbase(**item) for item in self.vin]
            else:
                self.vin = [BtcVIn(**item) for item in self.vin]

        if self.vout and not isinstance(self.vout[0], BtcVOut):
            self.vout = [BtcVOut(**item) for item in self.vout]


# noinspection SpellCheckingInspection
@dataclass
class BtcBlock:
    hash: str  # (string) the block hash (same as provided)
    confirmations: int  # (numeric) The number of confirmations, or -1 if the block is not on the main chain
    size: int  # (numeric) The block size
    strippedsize: int  # (numeric) The block size excluding witness data
    weight: int  # (numeric) The block weight as defined in BIP 141
    height: int  # (numeric) The block height or index
    version: int  # (numeric) The block version
    versionHex: str  # (string) The block version formatted in hexadecimal
    merkleroot: str  # (string) The merkle root
    tx: List[Union[str, dict]]  # (array of string) The transaction ids
    time: int  # (numeric) The block time in seconds since epoch (Jan 1 1970 GMT)
    mediantime: int  # (numeric) The median block time in seconds since epoch (Jan 1 1970 GMT)
    nonce: int  # (numeric) The nonce
    bits: str  # (string) The bits
    difficulty: float  # (numeric) The difficulty
    chainwork: str  # (string) Expected number of hashes required to produce the chain up to this block (in hex)
    nTx: int  # (numeric) The number of transactions in the block.
    previousblockhash: str = None  # (string) The hash of the previous block
    nextblockhash: str = None  # (string) The hash of the next block


class BitcoinDaemonProvider(Provider):
    def __init__(self, chain: str, network: str, url: str, auth: HTTPBasicAuth):
        super().__init__(chain, network)
        self.rpc = AsyncBitcoreDeamon(url, auth=auth)

    @property
    def type(self) -> ProviderType:
        return ProviderType.UTXO

    async def __aenter__(self):
        await self.rpc.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.rpc.__aexit__(exc_type, exc_val, exc_tb)

    async def _call(self, cls: Type[T], method: str, *params) -> T:
        res = await self.rpc.call(method, *params)
        res.raise_for_status()
        return await self._load(cls, res)

    @staticmethod
    async def _load(cls: Type[T], res: Response) -> T:
        if cls == Any:
            return res.json()
        else:
            if typing_inspect.get_origin(cls) == list:
                cls, = typing_inspect.get_args(cls)
                many = True
            else:
                many = False

            schema = get_schema(cls, many=many)
            obj = schema.load(res.json())
            return cast(T, obj)

    def _cast_block(self, block: BtcBlock) -> Block:
        block_time = datetime.utcfromtimestamp(block.time)

        return Block(
            _id="",
            chain=self.chain,
            network=self.network,
            confirmations=block.confirmations,
            height=block.height,
            hash=block.hash,
            version=block.version,
            merkleRoot=block.merkleroot,
            time=block_time.isoformat(),
            timeNormalized=block_time.isoformat(),  # ?
            nonce=block.nonce,
            previousBlockHash=block.previousblockhash,
            nextBlockHash=block.nextblockhash,
            transactionCount=len(block.tx),  # block.transactionCount
            size=block.size,
            bits=int(block.bits, 16),
            reward=-1,  # block.reward,
            processed=None,
        )

    def _cast_transaction(self, transaction: BtcTransaction, block: Union[BtcBlock, Block]) -> Transaction:
        return Transaction(
            _id="",
            txid=transaction.txid,
            chain=self.chain,
            network=self.network,
            blockHeight=block.height,
            blockHash=transaction.blockhash,
            blockTime=datetime.utcfromtimestamp(transaction.blocktime).isoformat() if transaction.blocktime else None,
            # TODO: normalized in block
            blockTimeNormalized=datetime.utcfromtimestamp(
                transaction.blocktime).isoformat() if transaction.blocktime else None,
            coinbase=transaction.is_coinbase(),
            fee=-1,  # "transaction.fee",  TODO: fee
            size=transaction.size,
            locktime=transaction.locktime,
            inputCount=len(transaction.vin),
            outputCount=len(transaction.vout),
            value=sum(item.value for item in transaction.vout),
            confirmations=transaction.confirmations,
        )

    async def _get_block(self, block_id: Union[str, int], *, verbosity: int) -> BtcBlock:
        if isinstance(block_id, int):
            block_hash = await self.rpc.getblockhash(int(block_id))
        else:
            block_hash = block_id

        block = await self.rpc.getblock(block_hash, verbosity=verbosity)
        assert isinstance(block, dict)

        return BtcBlock(**block)

    async def get_block(self, block_id: Union[str, int]) -> Block:
        block = await self._get_block(block_id, verbosity=1)
        return self._cast_block(block)

    async def get_full_block(self, block_id: str) -> Tuple[Block, List[Transaction]]:
        block = await self._get_block(block_id, verbosity=2)
        txs = []

        for transaction in block.tx:
            transaction = BtcTransaction(**transaction)
            transaction = self._cast_transaction(transaction, block)
            txs.append(transaction)

        block = self._cast_block(block)
        return block, txs

    async def get_transaction(self, tx_id: str) -> Transaction:
        transaction = await self.rpc.getrawtransaction(tx_id)
        assert isinstance(transaction, dict)

        transaction = BtcTransaction(**transaction)
        block = await self.get_block(transaction.blockhash)
        return self._cast_transaction(transaction, block)

    async def get_local_tip(self) -> Block:
        block_hash = await self.rpc.getbestblockhash()
        return await self.get_block(block_hash)
