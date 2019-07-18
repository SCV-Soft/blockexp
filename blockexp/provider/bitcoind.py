from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Union, Any, List, Optional

from pymongo import DESCENDING, ASCENDING, InsertOne, UpdateMany, UpdateOne
from requests.auth import HTTPBasicAuth

from .base import Provider, ProviderType, SteamingFindOptions, DailyTransactions, Direction, RawProvider
from ..error import BlockNotFound, TransactionNotFound, WalletNotFound
from ..ext.database import MongoDatabase, MongoCollection, bulk_write_for
from ..model import Block, Transaction, EstimateFee, TransactionId, CoinListing, Authhead, Balance, Coin, Wallet, \
    WalletAddress, WalletCheckResult
from ..proxy.bitcoind import AsyncBitcoinDeamon
from ..proxy.jsonrpc import JSONRPCError
from ..utils import asrow


@dataclass
class BtcVInCoinbase:
    coinbase: str
    sequence: int


@dataclass
class BtcScriptSig:
    asm: str
    hex: str


@dataclass
class BtcVIn:
    txid: str
    vout: int
    scriptSig: BtcScriptSig
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
    address: str = None
    addresses: List[str] = field(default_factory=list)
    wallets: List[str] = field(default_factory=list)

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


class BitcoinDaemonProvider(RawProvider):
    def __init__(self, chain: str, network: str, url: str, auth: HTTPBasicAuth):
        super().__init__(chain, network)
        self.rpc = AsyncBitcoinDeamon(url, auth=auth)
        self.is_legacy_getblock = None

    @property
    def type(self) -> ProviderType:
        return ProviderType.UTXO

    async def __aenter__(self):
        await self.rpc.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.rpc.__aexit__(exc_type, exc_val, exc_tb)

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
            time=block_time,
            timeNormalized=block_time,  # ?
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
            address=transaction.address,
            addresses=transaction.addresses,
            wallets=transaction.wallets,
        )

    async def _get_block(self, block_id: Union[str, int], *, verbosity: int) -> BtcBlock:
        if isinstance(block_id, int):
            block_hash = await self.rpc.getblockhash(int(block_id))
        else:
            block_hash = block_id

        if self.is_legacy_getblock is None:
            test_hash = await self.rpc.getbestblockhash()

            try:
                await self.rpc.getblock(test_hash, True)
            except JSONRPCError:
                # TODO: failure test function
                raise
            else:
                try:
                    await self.rpc.getblock(test_hash, verbosity)
                except JSONRPCError as e:
                    if e.code == -1:
                        self.is_legacy_getblock = True
                else:
                    self.is_legacy_getblock = False

        if self.is_legacy_getblock:
            if verbosity == 0:
                block = await self.rpc.getblock(block_hash, verbosity=False)
            elif verbosity == 1:
                block = await self.rpc.getblock(block_hash, verbosity=True)
            elif verbosity == 2:
                block = await self.rpc.getblock(block_hash, verbosity=True)

                txs = []
                for txid in block['tx']:
                    try:
                        tx = await self.rpc.getrawtransaction(txid, verbose=True)
                        tx = self._convert_raw_transaction(tx)
                        txs.append(tx)
                    except JSONRPCError as e:
                        if e.code == -5:
                            # TODO: ?
                            print('txid', txid, 'not found')
                        else:
                            raise

                block['tx'] = txs
            else:
                raise ValueError
        else:
            block = await self.rpc.getblock(block_hash, verbosity=verbosity)
            if 'tx' in block and block['tx'] and isinstance(block['tx'][0], dict):
                block['tx'] = [self._convert_raw_transaction(tx) for tx in block['tx']]

        assert isinstance(block, dict)
        return self._convert_raw_block(block)

    def _convert_raw_transaction(self, transaction: dict) -> BtcTransaction:
        return BtcTransaction(**transaction)

    def _convert_raw_block(self, block: dict) -> BtcBlock:
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

    async def get_fee(self, target: int) -> EstimateFee:
        return EstimateFee(**(await self.rpc.estimatesmartfee(target)))


class JackDaemonProvider(BitcoinDaemonProvider):
    def _convert_raw_transaction(self, transaction: dict) -> BtcTransaction:
        transaction['hash'] = transaction['txid']
        transaction['vsize'] = transaction['size']
        transaction['weight'] = -1
        return BtcTransaction(**transaction)

    def _convert_raw_block(self, block: dict) -> BtcBlock:
        del block['acc_checkpoint']
        del block['modifier']
        del block['moneysupply']
        del block['zJACKsupply']
        block['strippedsize'] = block['size']
        block['weight'] = -1
        block['versionHex'] = '-'
        block['nTx'] = len(block['tx'])

        return BtcBlock(**block)


class BitcoinMongoProvider(Provider):
    def __init__(self, chain: str, network: str, database: MongoDatabase, provider: BitcoinDaemonProvider):
        super().__init__(chain, network)
        self.database = database
        self.provider = provider

    @property
    def rpc(self) -> AsyncBitcoinDeamon:
        return self.provider.rpc

    def convert_raw_block(self, raw_block: dict, tip: Block = None) -> Block:
        block = Block(**raw_block, chain=self.chain, network=self.network)
        if tip is not None:
            block.confirmations = tip.height - block.height + 1

        return block

    def convert_raw_transaction(self, raw_transaction: dict, tip: Block = None) -> Transaction:
        raw_transaction.pop('chain', None)
        raw_transaction.pop('network', None)

        transaction = Transaction(**raw_transaction, chain=self.chain, network=self.network)
        if tip is not None:
            transaction.confirmations = tip.height - transaction.blockHeight + 1

        return transaction

    def convert_raw_coin(self, raw_coin: dict, tip: Block = None) -> Coin:
        coin = Coin(**raw_coin, chain=self.chain, network=self.network)
        if tip is not None:
            coin.confirmations = tip.height - coin.mintHeight + 1

        return coin

    def convert_raw_wallet(self, raw_wallet: dict) -> Wallet:
        return Wallet(**raw_wallet, chain=self.chain, network=self.network)

    def convert_raw_wallet_address(self, raw_wallet_address: dict) -> WalletAddress:
        return WalletAddress(**raw_wallet_address, chain=self.chain, network=self.network)

    @property
    def _collection_key(self) -> str:
        return f'{self.chain}:{self.network}'

    @property
    def block_collection(self) -> MongoCollection:
        return self.database[f'{self._collection_key}:blocks']

    @property
    def tx_collection(self) -> MongoCollection:
        return self.database[f'{self._collection_key}:transactions']

    @property
    def coin_collection(self) -> MongoCollection:
        return self.database[f'{self._collection_key}:coins']

    @property
    def wallet_collection(self) -> MongoCollection:
        return self.database[f'{self._collection_key}:wallets']

    @property
    def wallet_address_collection(self) -> MongoCollection:
        return self.database[f'{self._collection_key}:walletaddresses']

    async def streaming(self,
                        collection: MongoCollection,
                        query: dict,
                        find_options: SteamingFindOptions) -> List[dict]:
        if find_options.limit is None:
            find_options.limit = 0

        query = query.copy()

        paging = find_options.paging
        if paging is not None:
            # TODO: vaild attribute for model
            if find_options.since is not None:
                if find_options.direction == Direction.ASCENDING:
                    query[paging] = {'$gt': find_options.since}
                elif find_options.direction == Direction.DESCENDING:
                    query[paging] = {'$lt': find_options.since}

        cursor = collection.find(query, limit=find_options.limit)

        if find_options.sort is not None:
            cursor = cursor.sort(find_options.sort)

        return await cursor.to_list(None)

    async def stream_address_transactions(self,
                                          address: str,
                                          unspent: bool,
                                          find_options: SteamingFindOptions) -> List[Transaction]:
        query = {'wallets': address}
        if unspent is not None:
            if unspent:
                query['spentHeight'] = {'$gte': 0}
            else:
                query['spentHeight'] = {'$lt': 0}

        tip = await self.get_local_tip()
        raw_transactions = await self.streaming(self.tx_collection, query, find_options)
        return [self.convert_raw_transaction(raw_transaction, tip=tip)
                for raw_transaction in raw_transactions]

    async def stream_address_utxos(self, address: str, unspent: bool, find_options: SteamingFindOptions) -> List[Any]:
        query = {'wallets': address}
        if unspent:
            query['spentHeight'] = {'$lt': 0}

        tip = await self.get_local_tip()
        raw_coins = await self.streaming(self.coin_collection, query, find_options)
        return [self.convert_raw_coin(raw_coin, tip=tip)
                for raw_coin in raw_coins]

    async def _get_balance_in_cursor(self, raw_coins) -> Balance:
        confirmed = 0
        unconfirmed = 0
        balance = 0

        async for raw_coin in raw_coins:
            value = raw_coin['value']

            is_confirmed = raw_coin['mintHeight'] >= 0  # always true
            if is_confirmed:
                confirmed += value
            else:
                unconfirmed += value

            balance += value

        return Balance(confirmed=confirmed, unconfirmed=unconfirmed, balance=balance)

    async def get_balance_for_address(self, address: str) -> Balance:
        raw_coins = self.coin_collection.find({
            'address': address,
            'spentHeight': {'$lt': 0},
            'mintHeight': {'$gt': -3},
        })

        return await self._get_balance_in_cursor(raw_coins)

    async def stream_blocks(self,
                            since_block: Union[str, int] = None,
                            start_date: str = None,
                            end_date: str = None,
                            date: str = None,
                            *,
                            find_options: SteamingFindOptions) -> List[Block]:
        query = {}

        if since_block is None:
            pass
        elif isinstance(since_block, str):
            query['hash'] = since_block
        elif isinstance(since_block, int):
            query['height'] = {'$gt': since_block}

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

        if find_options is None:
            find_options = SteamingFindOptions()

        find_options.sort = [('height', DESCENDING)]

        tip = await self.get_local_tip()
        raw_blocks = await self.streaming(self.block_collection, query, find_options)
        return [self.convert_raw_block(raw_block, tip=tip)
                for raw_block in raw_blocks]

    async def get_block(self, block_id: Union[str, int]) -> Block:
        raw_block: Optional[dict] = await self.get_raw_block(block_id)
        if raw_block is None:
            raise BlockNotFound(block_id)

        return self.convert_raw_block(raw_block)

    async def get_raw_block(self, block_id: Union[str, int]) -> Optional[dict]:
        if isinstance(block_id, int):
            return await self.block_collection.find_one({'height': block_id})
        elif isinstance(block_id, str):
            return await self.block_collection.find_one({'hash': block_id})
        else:
            raise TypeError

    async def stream_transactions(self,
                                  block_height: Optional[int] = None,
                                  block_hash: Optional[str] = None,
                                  *,
                                  find_options: SteamingFindOptions) -> List[Transaction]:
        query = {}

        if block_height is not None:
            query['blockHeight'] = block_height

        if block_hash is not None:
            query['blockHash'] = block_hash

        tip = await self.get_local_tip()
        raw_transactions = await self.streaming(self.tx_collection, query, find_options)
        return [self.convert_raw_transaction(raw_transaction, tip=tip)
                for raw_transaction in raw_transactions]

    async def get_transaction(self, tx_id: str) -> Transaction:
        raw_tx: Optional[dict] = await self.tx_collection.find_one({'txid': tx_id})
        if raw_tx is None:
            raise TransactionNotFound(tx_id)

        return self.convert_raw_transaction(raw_tx, None)

    async def get_authhead(self, tx_id: str) -> Authhead:
        raise NotImplementedError("NOT IMPLEMENTED YET")

    async def create_wallet(self,
                            name: str,
                            pub_key: str,
                            path: Optional[str],
                            single_address: Optional[bool]) -> Wallet:
        wallet = Wallet(
            chain=self.chain,
            network=self.network,
            name=name,
            pubKey=pub_key,
            path=path,
            singleAddress=single_address,
        )

        await self.wallet_collection.find_one_and_update(
            filter={'pubKey': wallet.pubKey},
            update={'$set': asrow(wallet)},
            upsert=True,
        )

        return wallet

    async def wallet_check(self, wallet: Wallet) -> WalletCheckResult:
        assert wallet._id is not None

        raw_wallet_addresses = self.wallet_address_collection.find({'wallet': wallet._id})

        last_address = None
        total = 0
        async for raw_wallet_address in raw_wallet_addresses:
            wallet_address = self.convert_raw_wallet_address(raw_wallet_address)
            last_address = address = wallet_address.address
            total += sum(address.encode('ascii'))

        total %= 9007199254740991  # Number.MAX_SAFE_INTEGER
        return WalletCheckResult(lastAddress=last_address, sum=total)

    async def stream_missing_wallet_addresses(self, wallet: Wallet):
        assert wallet._id is not None

        raw_coins = self.coin_collection.find({
            'wallets': wallet._id,
            'spentHeight': {'$gte': 0},
        })

        seen = set()
        total_missing_value = 0
        missing_addresses = set()

        async for raw_coin in raw_coins:
            coin = self.convert_raw_coin(raw_coin)
            if coin.spentTxid not in seen:
                seen.add(coin.spentTxid)

                missings = []
                raw_spends = self.coin_collection.find({'spentTxid': coin.spentTxid})
                async for raw_spend in raw_spends:
                    spend = self.convert_raw_coin(raw_spend)
                    if wallet._id not in coin.wallets:
                        total_missing_value += spend.value
                        missing = asrow(coin)
                        missing['expected'] = wallet._id

                        missing_addresses.update(spend.addresses)
                        missings.append(missing)

        # TODO: streamMissingWalletAddresses [???

    async def stream_wallet_addresses(self, wallet: Wallet, limit: int) -> List[WalletAddress]:
        wallet_addresses = []
        async for raw_wallet_address in self.wallet_address_collection.find({'wallet': wallet._id}):
            wallet_address = self.convert_raw_wallet_address(raw_wallet_address)
            wallet_addresses.append(wallet_address)

        return wallet_addresses

    async def update_wallet(self, wallet: Wallet, addresses: List[str]):
        exist_addresses = {
            item.get('address', self.convert_raw_wallet_address(item).address)  # ?
            async for item in self.wallet_address_collection.find({
                'wallet': wallet._id,
                'address': {'$in': addresses},
            })
        }

        addresses = [
            address
            for address in addresses
            if address not in exist_addresses
        ]

        async with bulk_write_for(self.wallet_address_collection, ordered=False) as db_ops:
            for address in addresses:
                db_ops.append(InsertOne({
                    'wallet': wallet._id,
                    'address': address,
                    'processed': False,
                }))

        async with bulk_write_for(self.coin_collection, ordered=False) as db_ops:
            for address in addresses:
                db_ops.append(UpdateMany(
                    filter={'address': address},
                    update={'$addToSet': {'wallets': wallet._id}}
                ))

        txids = set()
        async for item in self.coin_collection.find(
                filter={'address': {'$in': addresses}},
                projection={'mintTxid': True, 'spentTxid': True}
        ):
            for txid in item.get('mintTxid', None), item.get('spentTxid', None):
                if txid is not None:
                    txids.add(txid)

        await self.tx_collection.update_many(
            filter={'txid': {'$in': list(txids)}},
            update={'$addToSet': {'wallets': wallet._id}},
        )

        async with bulk_write_for(self.wallet_address_collection, ordered=False) as db_ops:
            for address in addresses:
                db_ops.append(UpdateOne(
                    filter={
                        'wallet': wallet._id,
                        'address': address,
                    },
                    update={
                        '$set': {
                            'processed': True,
                        }
                    },
                ))

    async def stream_wallet_transactions(self,
                                         wallet: Wallet,
                                         start_block: int = None,
                                         end_block: int = None,
                                         start_date: str = None,
                                         end_date: str = None,
                                         *,
                                         find_options: SteamingFindOptions) -> List[Transaction]:
        assert wallet._id is not None

        query = {'wallets': wallet._id}

        if start_block is not None:
            query.setdefault('blockHeight', {}).update({'$gte': start_block})

        if end_block is not None:
            query.setdefault('blockHeight', {}).update({'$lte': end_block})

        if start_date:
            start_date = datetime.fromisoformat(start_date)
            query.setdefault('blockTimeNormalized', {}).update({'$gt': start_date.isoformat()})

        if end_date:
            end_date = datetime.fromisoformat(end_date)
            query.setdefault('blockTimeNormalized', {}).update({'$lt': end_date.isoformat()})

        if find_options is None:
            find_options = SteamingFindOptions()

        find_options.sort = [('blockTimeNormalized', ASCENDING)]

        tip = await self.get_local_tip()
        raw_transactions = await self.streaming(self.tx_collection, query, find_options)
        return [self.convert_raw_transaction(raw_transaction, tip=tip)
                for raw_transaction in raw_transactions]

    async def get_wallet_balance(self, wallet: Wallet) -> Balance:
        raw_coins = self.coin_collection.find({
            'wallets': wallet._id,
            'spentHeight': {'$lt', 0},
            'mintHeight': {'$gt': -3},
        })

        return await self._get_balance_in_cursor(raw_coins)

    async def get_wallet_balance_at_time(self, wallet: Wallet, time: str) -> Balance:
        raw_block = await self.block_collection.find_one({
            'timeNormalized': {'$lte', datetime.fromisoformat(time)}
        }, sort=[('timeNormalized', DESCENDING)])

        block = self.convert_raw_block(raw_block)

        raw_coins = self.coin_collection.find({
            'wallets': wallet._id,
            '$or': [
                {'spentHeight': {'$gt', block.height}},
                {'spentHeight': -2},
            ],
            'mintHeight': {'$lte': block.height},
        })

        return await self._get_balance_in_cursor(raw_coins)

    async def stream_wallet_utxos(self,
                                  wallet: Wallet,
                                  limit: int = None,
                                  include_spent: bool = False) -> List[Coin]:
        raw_coins = self.coin_collection.find({
            'wallets': wallet._id,
            'spentHeight': -2,
            'mintHeight': {'$gte': 0},
        })

        tip = await self.get_local_tip()

        return [self.convert_raw_coin(raw_coin, tip=tip)
                async for raw_coin in raw_coins]

    async def get_wallet(self, pub_key: str) -> Wallet:
        raw_wallet = await self.wallet_collection.find_one({'pubKey': pub_key})
        if not raw_wallet:
            raise WalletNotFound(pub_key)

        return self.convert_raw_wallet(raw_wallet)

    async def get_fee(self, target: int) -> EstimateFee:
        return await self.provider.get_fee(target)

    async def broadcast_transaction(self, raw_tx: str) -> TransactionId:
        txid = await self.rpc.sendrawtransaction(raw_tx)
        return TransactionId(txid)

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        inputs = self.coin_collection.find({'spentTxid': tx_id})
        outputs = self.coin_collection.find({'mintTxid': tx_id})

        return CoinListing(
            inputs=[self.convert_raw_coin(raw_coin) async for raw_coin in inputs],
            outputs=[self.convert_raw_coin(raw_coin) async for raw_coin in outputs],
        )

    async def get_daily_transactions(self) -> DailyTransactions:
        results = self.block_collection.aggregate([
            {'$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$timeNormalized',
                    }
                },
                'transactionCount': {
                    '$sum': '$transactionCount',
                }
            }},
            {'$project': {
                '_id': 0,
                'date': '$_id',
                'transactionCount': '$transactionCount',
            }},
            {'$sort': {
                'date': 1,
            }},
        ])

        return DailyTransactions(
            results=[result async for result in results],
            chain=self.chain,
            network=self.network,
        )

    async def get_local_tip(self) -> Block:
        raw_block: Optional[dict] = await self.block_collection.find_one(sort=[('height', DESCENDING)])
        if raw_block is None:
            raise BlockNotFound(None)

        return self.convert_raw_block(raw_block)

    async def get_locator_hashes(self):
        raise NotImplementedError
