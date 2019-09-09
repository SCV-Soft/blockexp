from datetime import datetime, timedelta
from typing import Union, List, Optional, TypeVar

from pymongo import DESCENDING, ASCENDING, InsertOne, UpdateMany, UpdateOne

from .accessor import BtcDaemonAccessor
from .bitcoind import AsyncBitcoinDeamon
from .mongo import BtcMongoDatabase
from ..utils.mongo import get_balance
from ...database import bulk_write_for
from ...error import BlockNotFound, TransactionNotFound, WalletNotFound
from ...model import Block, Transaction, EstimateFee, TransactionId, CoinListing, Authhead, Balance, Coin, Wallet, \
    WalletAddress, WalletCheckResult, DailyTransactions
from ...model.options import SteamingFindOptions
from ...types import Provider
from ...utils import asrow

T = TypeVar('T')
MAX_SAFE_INTEGER = 9007199254740991  # Number.MAX_SAFE_INTEGER


class BtcMongoProvider(Provider):
    def __init__(self, chain: str, network: str, db: BtcMongoDatabase, accessor: BtcDaemonAccessor):
        super().__init__(chain, network)
        self.db = db
        self.accessor = accessor

    @property
    def rpc(self) -> AsyncBitcoinDeamon:
        return self.accessor.rpc

    async def stream_address_transactions(self,
                                          address: str,
                                          unspent: bool,
                                          find_options: SteamingFindOptions) -> List[Transaction]:
        query = {'addresses': address}
        if unspent is not None:
            if unspent:
                query['spentHeight'] = {'$lt': 0}
            else:
                query['spentHeight'] = {'$gte': 0}

        return await self.db.tx_collection.streaming(query, find_options)

    async def stream_address_utxos(self, address: str, unspent: bool, find_options: SteamingFindOptions) -> List[Coin]:
        query = {'addresses': address}
        if unspent is not None:
            if unspent:
                query['spentHeight'] = {'$lt': 0}
            else:
                query['spentHeight'] = {'$gte': 0}

        return await self.db.coin_collection.streaming(query, find_options)

    async def get_balance_for_address(self, address: str) -> Balance:
        raw_coins = await self.db.coin_collection.fetch_all({
            'address': address,
            'spentHeight': {'$lt': 0},
            'mintHeight': {'$gt': -3},
        })

        return get_balance(raw_coins)

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

        return await self.db.block_collection.streaming(query, find_options)

    async def get_block(self, block_id: Union[str, int]) -> Block:
        if isinstance(block_id, int):
            block = await self.db.block_collection.fetch_one({'height': block_id})  # Block.height
        elif isinstance(block_id, str):
            block = await self.db.block_collection.fetch_one({'hash': block_id})  # Block.hash
        else:
            raise TypeError

        if block is None:
            raise BlockNotFound(block_id)

        return block

    async def get_raw_block(self, block_id: Union[str, int]) -> dict:
        if isinstance(block_id, int):
            raw_block = await self.db.raw_block_collection.fetch_one({'height': block_id})  # BtcBlock.height
        elif isinstance(block_id, str):
            raw_block = await self.db.raw_block_collection.fetch_one({'hash': block_id})  # BtcBlock.hash
        else:
            raise TypeError

        if raw_block is None:
            raise BlockNotFound(block_id)

        return raw_block

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

        return await self.db.tx_collection.streaming(query, find_options)

    async def get_transaction(self, tx_id: str) -> Transaction:
        transaction = await self.db.tx_collection.fetch_one({'txid': tx_id})
        if transaction is None:
            raise TransactionNotFound(tx_id)

        return transaction

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

        await self.db.wallet_collection.find_one_and_update(
            filter={'pubKey': wallet.pubKey},
            update={'$set': asrow(wallet)},
            upsert=True,
        )

        return wallet

    async def wallet_check(self, wallet: Wallet) -> WalletCheckResult:
        assert wallet._id is not None

        raw_wallet_addresses = self.db.wallet_address_collection.find({'wallet': wallet._id})

        last_address = None
        total = 0
        async for raw_wallet_address in raw_wallet_addresses:
            wallet_address = self.db.convert_raw_wallet_address(raw_wallet_address)
            last_address = address = wallet_address.address
            total += sum(address.encode('ascii'))

        total %= MAX_SAFE_INTEGER
        return WalletCheckResult(lastAddress=last_address, sum=total)

    async def stream_missing_wallet_addresses(self, wallet: Wallet):
        assert wallet._id is not None

        raw_coins = self.db.coin_collection.find({
            'wallets': wallet._id,
            'spentHeight': {'$gte': 0},
        })

        seen = set()
        total_missing_value = 0
        missing_addresses = set()

        async for raw_coin in raw_coins:
            coin = self.db.convert_raw_coin(raw_coin)
            if coin.spentTxid not in seen:
                seen.add(coin.spentTxid)

                missings = []
                raw_spends = self.db.coin_collection.find({'spentTxid': coin.spentTxid})
                async for raw_spend in raw_spends:
                    spend = self.db.convert_raw_coin(raw_spend)
                    if wallet._id not in coin.wallets:
                        total_missing_value += spend.value
                        missing = asrow(coin)
                        missing['expected'] = wallet._id

                        missing_addresses.update(spend.addresses)
                        missings.append(missing)

        # TODO: streamMissingWalletAddresses [???

    async def stream_wallet_addresses(self, wallet: Wallet, limit: int) -> List[WalletAddress]:
        wallet_addresses = []
        async for raw_wallet_address in self.db.wallet_address_collection.find({'wallet': wallet._id}):
            wallet_address = self.db.convert_raw_wallet_address(raw_wallet_address)
            wallet_addresses.append(wallet_address)

        return wallet_addresses

    async def update_wallet(self, wallet: Wallet, addresses: List[str]):
        exist_addresses = {
            item.get('address', self.db.convert_raw_wallet_address(item).address)  # ?
            async for item in self.db.wallet_address_collection.find({
                'wallet': wallet._id,
                'address': {'$in': addresses},
            })
        }

        addresses = [
            address
            for address in addresses
            if address not in exist_addresses
        ]

        async with bulk_write_for(self.db.wallet_address_collection, ordered=False) as db_ops:
            for address in addresses:
                db_ops.append(InsertOne({
                    'wallet': wallet._id,
                    'address': address,
                    'processed': False,
                }))

        async with bulk_write_for(self.db.coin_collection, ordered=False) as db_ops:
            for address in addresses:
                db_ops.append(UpdateMany(
                    filter={'address': address},
                    update={'$addToSet': {'wallets': wallet._id}}
                ))

        txids = set()
        async for item in self.db.coin_collection.find(
                filter={'address': {'$in': addresses}},
                projection={'mintTxid': True, 'spentTxid': True}
        ):
            for txid in item.get('mintTxid', None), item.get('spentTxid', None):
                if txid is not None:
                    txids.add(txid)

        await self.db.tx_collection.update_many(
            filter={'txid': {'$in': list(txids)}},
            update={'$addToSet': {'wallets': wallet._id}},
        )

        async with bulk_write_for(self.db.wallet_address_collection, ordered=False) as db_ops:
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

        return await self.db.tx_collection.streaming(query, find_options)

    async def get_wallet_balance(self, wallet: Wallet) -> Balance:
        return get_balance(await self.db.coin_collection.fetch_all({
            'wallets': wallet._id,
            'spentHeight': {'$lt', 0},
            'mintHeight': {'$gt': -3},
        }))

    async def get_wallet_balance_at_time(self, wallet: Wallet, time: str) -> Balance:
        block = await self.db.block_collection.fetch_one({
            'timeNormalized': {'$lte', datetime.fromisoformat(time)}
        }, sort=[('timeNormalized', DESCENDING)])

        return get_balance(await self.db.coin_collection.fetch_all({
            'wallets': wallet._id,
            '$or': [
                {'spentHeight': {'$gt', block.height}},
                {'spentHeight': -2},
            ],
            'mintHeight': {'$lte': block.height},
        }))

    async def stream_wallet_utxos(self,
                                  wallet: Wallet,
                                  limit: int = None,
                                  include_spent: bool = False) -> List[Coin]:
        return await self.db.coin_collection.fetch_all({
            'wallets': wallet._id,
            'spentHeight': -2,
            'mintHeight': {'$gte': 0},
        })

    async def get_wallet(self, pub_key: str) -> Wallet:
        wallet = await self.db.wallet_collection.fetch_one({'pubKey': pub_key})
        if not wallet:
            raise WalletNotFound(pub_key)

        return wallet

    async def get_fee(self, target: int) -> EstimateFee:
        return await self.accessor.get_fee(target)

    async def broadcast_transaction(self, raw_tx: str) -> TransactionId:
        txid = await self.rpc.sendrawtransaction(raw_tx)
        return TransactionId(txid)

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        return CoinListing(
            inputs=(await self.db.coin_collection.fetch_all({'spentTxid': tx_id})),
            outputs=(await self.db.coin_collection.fetch_all({'mintTxid': tx_id})),
        )

    async def get_daily_transactions(self) -> DailyTransactions:
        results = self.db.block_collection.aggregate([
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
        return await self.db.fetch_block_tip()

    async def get_locator_hashes(self):
        raise NotImplementedError
