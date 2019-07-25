from datetime import datetime, timedelta
from typing import Union, Any, List, Optional

from pymongo import DESCENDING, ASCENDING, InsertOne, UpdateMany, UpdateOne

from .accessor import BitcoinDaemonAccessor
from .bitcoind import AsyncBitcoinDeamon
from ...error import BlockNotFound, TransactionNotFound, WalletNotFound
from ...ext.database import MongoDatabase, MongoCollection, bulk_write_for
from ...model import Block, Transaction, EstimateFee, TransactionId, CoinListing, Authhead, Balance, Coin, Wallet, \
    WalletAddress, WalletCheckResult, DailyTransactions
from ...model.options import Direction, SteamingFindOptions
from ...types import Provider
from ...utils import asrow


class BitcoinMongoProvider(Provider):
    def __init__(self, chain: str, network: str, database: MongoDatabase, accessor: BitcoinDaemonAccessor):
        super().__init__(chain, network)
        self.database = database
        self.accessor = accessor

    @property
    def rpc(self) -> AsyncBitcoinDeamon:
        return self.accessor.rpc

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
        query = {'addresses': address}
        if unspent is not None:
            if unspent:
                query['spentHeight'] = {'$lt': 0}
            else:
                query['spentHeight'] = {'$gte': 0}

        tip = await self.get_local_tip()
        raw_transactions = await self.streaming(self.tx_collection, query, find_options)
        return [self.convert_raw_transaction(raw_transaction, tip=tip)
                for raw_transaction in raw_transactions]

    async def stream_address_utxos(self, address: str, unspent: bool, find_options: SteamingFindOptions) -> List[Any]:
        query = {'addresses': address}
        if unspent is not None:
            if unspent:
                query['spentHeight'] = {'$lt': 0}
            else:
                query['spentHeight'] = {'$gte': 0}

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
        return await self.accessor.get_fee(target)

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
