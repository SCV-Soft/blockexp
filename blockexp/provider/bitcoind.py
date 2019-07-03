from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Union, Type, TypeVar, cast, Any, List, Optional

import typing_inspect
from pymongo import DESCENDING
from requests.auth import HTTPBasicAuth
from requests_async import Response

from starlette_typed.marshmallow import build_schema, Schema
from .base import Provider, ProviderType, SteamingFindOptions
from ..ext.database import MongoDatabase, MongoCollection
from ..model import Block, Transaction, EstimateFee, TransactionId, CoinListing, Authhead, AddressBalance, Coin
from ..proxy.bitcoind import AsyncBitcoreDeamon

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
class BtcScriptPubKey:
    type: str
    asm: str
    hex: str
    reqSigs: int = None
    addresses: List[str] = None


@dataclass
class BtcVOut:
    value: float
    n: int
    scriptPubKey: Union[dict, BtcScriptPubKey]

    def __post_init__(self):
        if not isinstance(self.scriptPubKey, BtcScriptPubKey):
            self.scriptPubKey = BtcScriptPubKey(**self.scriptPubKey)


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
    tx: List[Union[str, dict, BtcTransaction]]  # (array of string) The transaction ids
    time: int  # (numeric) The block time in seconds since epoch (Jan 1 1970 GMT)
    mediantime: int  # (numeric) The median block time in seconds since epoch (Jan 1 1970 GMT)
    nonce: int  # (numeric) The nonce
    bits: str  # (string) The bits
    difficulty: float  # (numeric) The difficulty
    chainwork: str  # (string) Expected number of hashes required to produce the chain up to this block (in hex)
    nTx: int  # (numeric) The number of transactions in the block.
    previousblockhash: str = None  # (string) The hash of the previous block
    nextblockhash: str = None  # (string) The hash of the next block

    def __post_init__(self):
        if self.tx and isinstance(self.tx[0], dict):
            self.tx = [BtcTransaction(**item) for item in self.tx]


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
            txid=transaction.txid,
            chain=self.chain,
            network=self.network,
            blockHeight=block.height,
            blockHash=block.hash,
            blockTime=datetime.utcfromtimestamp(block.time).isoformat() if block.time else None,
            blockTimeNormalized=datetime.utcfromtimestamp(block.time).isoformat() if block.time else None,
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

    async def get_raw_block(self, block_id: Union[str, int]) -> BtcBlock:
        return await self._get_block(block_id, verbosity=2)

    def convert_raw_block(self, raw_block: Any) -> Block:
        assert isinstance(raw_block, BtcBlock)
        return self._cast_block(raw_block)

    def convert_raw_transaction(self, raw_transaction: Any, raw_block: Any) -> Transaction:
        assert isinstance(raw_transaction, BtcTransaction)
        assert isinstance(raw_block, BtcBlock)
        return self._cast_transaction(raw_transaction, raw_block)

    async def get_transaction(self, tx_id: str) -> Transaction:
        transaction = await self.rpc.getrawtransaction(tx_id)
        assert isinstance(transaction, dict)

        transaction = BtcTransaction(**transaction)
        block = await self.get_block(transaction.blockhash)
        return self._cast_transaction(transaction, block)

    async def get_local_tip(self) -> Block:
        block_hash = await self.rpc.getbestblockhash()
        return await self.get_block(block_hash)


class BitcoinMongoProvider(Provider):
    def __init__(self, chain: str, network: str, database: MongoDatabase, provider: BitcoinDaemonProvider = None):
        super().__init__(chain, network)
        self.database = database
        self.provider = provider
        # TODO: cache tip for refresh confirm count

    def convert_raw_block(self, raw_block: Any, tip: Block = None) -> Block:
        return Block(**raw_block, chain=self.chain, network=self.network)

    def convert_raw_transaction(self, raw_transaction: Any, raw_block: Any) -> Transaction:
        return Transaction(**raw_transaction, chain=self.chain, network=self.network)

    def convert_raw_coin(self, raw_coin: dict) -> Coin:
        return Coin(**raw_coin, chain=self.chain, network=self.network)

    @property
    def _collection_key(self) -> str:
        return f'{self.chain}:{self.network}'

    @property
    def block_collection(self) -> MongoCollection:
        return self.database[f'blocks[{self._collection_key}]']

    @property
    def tx_collection(self) -> MongoCollection:
        return self.database[f'transactions[{self._collection_key}]']

    @property
    def coin_collection(self) -> MongoCollection:
        return self.database[f'coins[{self._collection_key}]']

    def cast_find_options(self, find_options: SteamingFindOptions) -> dict:
        find_options.limit = 10

        return {'limit': find_options.limit}

    async def stream_address_transactions(self,
                                          address: str,
                                          unspent: bool,
                                          find_options: SteamingFindOptions) -> List[Any]:
        raise NotImplementedError

    async def stream_address_utxos(self, address: str, unspent: bool, find_options: SteamingFindOptions) -> List[Any]:
        query = {'wallets': address}
        if unspent:
            query.update({'spentHeight': {'$lt': 0}})

        raw_coins = self.coin_collection.find(query, **self.cast_find_options(find_options))
        return [self.convert_raw_coin(raw_coin) async for raw_coin in raw_coins]

    async def get_balance_for_address(self, address: str) -> AddressBalance:
        raw_coins = self.coin_collection.find({
            'wallets': address,
            'spentHeight': {'$lt': 0},
            'mintHeight': {'$gt': -3},
        })

        confirmed = 0
        unconfirmed = 0
        balance = 0

        async for raw_coin in raw_coins:
            # TODO: satoshi or value?
            value = raw_coin['value']

            is_confirmed = raw_coin['mintHeight'] >= 0  # always true
            if is_confirmed:
                confirmed += value
            else:
                unconfirmed += value

            balance += value

        return AddressBalance(confirmed=confirmed, unconfirmed=unconfirmed, balance=balance)

    async def stream_blocks(self,
                            since_block: Union[str, int] = None,
                            start_date: str = None,
                            end_date: str = None,
                            date: str = None,
                            find_options: SteamingFindOptions[Block] = None) -> List[Block]:
        tip = await self.get_local_tip()
        query = {}

        if isinstance(since_block, str):
            query.update({'hash': since_block})
        elif isinstance(since_block, int):
            query.update({'height': {'$gt': since_block}})
        else:
            raise TypeError

        if start_date:
            start_date = datetime.fromisoformat(start_date)
            query.setdefault('time', {}).update({'$gt': start_date.isoformat()})

        if end_date:
            end_date = datetime.fromisoformat(end_date)
            query.setdefault('time', {}).update({'$lt': end_date.isoformat()})

        if date:
            date = datetime.fromisoformat(date)
            next_date = date + timedelta(days=1)
            query.setdefault('time', {}).update({
                '$gt': date.isoformat(),
                '$lt': next_date.isoformat(),
            })

        raw_blocks = self.block_collection.find(query, **self.cast_find_options(find_options))
        return [self.convert_raw_block(raw_block, tip=tip) async for raw_block in raw_blocks]

    async def get_block(self, block_id: Union[str, int]) -> Block:
        raw_block: Optional[dict] = await self.get_raw_block(block_id)
        if raw_block is None:
            raise KeyError(block_id)

        return self.convert_raw_block(raw_block)

    async def get_raw_block(self, block_id: Union[str, int]) -> Optional[dict]:
        if isinstance(block_id, int):
            block_height = block_id
            block: Optional[dict] = await self.block_collection.find_one({'height': block_height})
            return block
        elif isinstance(block_id, str):
            block_hash = block_id
            block: Optional[dict] = await self.block_collection.find_one({'hash': block_hash})
            return block
        else:
            raise TypeError

    async def stream_transactions(self,
                                  block_height: int,
                                  block_hash: str,
                                  find_options: SteamingFindOptions) -> List[Transaction]:
        raise NotImplementedError

    async def get_transaction(self, tx_id: str) -> Transaction:
        raw_tx: Optional[dict] = await self.tx_collection.find_one({'txid': tx_id})
        if raw_tx is None:
            raise KeyError(tx_id)

        return self.convert_raw_transaction(raw_tx, None)

    async def get_authhead(self, tx_id: str) -> Authhead:
        raise NotImplementedError

    async def create_wallet(self, name: str, pub_key: str, path: str, single_address: bool) -> Any:
        raise NotImplementedError

    async def wallet_check(self):
        raise NotImplementedError

    async def stream_missing_wallet_addresses(self):
        raise NotImplementedError

    async def update_wallet(self):
        raise NotImplementedError

    async def stream_wallet_transactions(self):
        raise NotImplementedError

    async def get_wallet_balance(self):
        raise NotImplementedError

    async def get_wallet_balance_at_time(self):
        raise NotImplementedError

    async def stream_wallet_utxos(self):
        raise NotImplementedError

    async def get_fee(self, target: int) -> EstimateFee:
        raise NotImplementedError

    async def broadcast_transaction(self, raw_tx: Any) -> TransactionId:
        raise NotImplementedError

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        inputs = self.coin_collection.find({'spentTxid': tx_id})
        outputs = self.coin_collection.find({'mintTxid': tx_id})

        return CoinListing(
            inputs=[self.convert_raw_coin(raw_coin) async for raw_coin in inputs],
            outputs=[self.convert_raw_coin(raw_coin) async for raw_coin in outputs],
        )

    async def get_daily_transactions(self) -> Any:
        raise NotImplementedError

    async def get_local_tip(self) -> Block:
        def sort(**data):
            return list(data.items())

        raw_block: Optional[dict] = await self.block_collection.find_one(sort=sort(height=DESCENDING))
        if raw_block is None:
            raise KeyError(None)

        return self.convert_raw_block(raw_block)

    async def get_locator_hashes(self):
        raise NotImplementedError
