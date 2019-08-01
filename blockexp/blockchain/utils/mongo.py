from collections import Callable
from typing import Optional, List, TypeVar, Generic

from ...database import MongoDatabase, MongoCollection
from ...model import Block, Transaction, Coin, Wallet, WalletAddress, Balance
from ...model.options import SteamingFindOptions, Direction
from ...types import Base

T = TypeVar('T')


def index(**data):
    return list(data.items())


class BlockchainMongoCollection(MongoCollection, Generic[T]):
    def __init__(self, collection: MongoCollection, converter: Callable, fetch_tip: Optional[Callable]):
        super().__init__(collection._collection, database=collection._database)
        self.converter = converter
        self.fetch_tip = fetch_tip

    async def _convert_all(self, cursor) -> List[T]:
        converter = self.converter
        tip = await self.fetch_tip() if self.fetch_tip is not None else None

        if tip is not None:
            return [converter(item, tip) async for item in cursor]
        else:
            return [converter(item) async for item in cursor]

    async def streaming(
            self,
            query: dict,
            find_options: SteamingFindOptions) -> List[T]:
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

        cursor = self.find(query, limit=find_options.limit)

        if find_options.sort is not None:
            cursor = cursor.sort(find_options.sort)

        return await self._convert_all(cursor)

    # noinspection PyShadowingBuiltins
    async def fetch_all(self, filter=None, projection=None, **kwargs) -> List[T]:
        items = self.find(filter, projection=projection, **kwargs)
        return await self._convert_all(items)

    # noinspection PyShadowingBuiltins
    async def fetch_one(self, filter=None, projection=None, **kwargs) -> Optional[T]:
        item: Optional[dict] = await self.find_one(filter, projection=projection, **kwargs)
        if item is None:
            return item

        return self.converter(item)


class BlockchainMongoDatabase(Base):
    def __init__(self, chain: str, network: str, database: MongoDatabase):
        super().__init__(chain, network)
        self.database = database

    @property
    def _collection_key(self) -> str:
        return f'{self.chain}:{self.network}'

    def new_collection(self, name: str, converter: Callable,
                       fetch_tip: Optional[Callable]) -> BlockchainMongoCollection:
        return BlockchainMongoCollection(self.database[f'{self._collection_key}:{name}'], converter, fetch_tip)

    async def create_indexes(self):
        raise NotImplementedError

    def convert_raw_block(self, raw_block: dict, tip: Block = None) -> Block:
        block = Block(**raw_block, chain=self.chain, network=self.network)
        if tip is not None:
            block.confirmations = tip.height - block.height + 1

        return block

    def convert_raw_transaction(self, raw_transaction: dict, tip: Block = None) -> Transaction:
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


def get_balance(raw_coins: List[dict]) -> Balance:
    confirmed = 0
    unconfirmed = 0
    balance = 0

    for raw_coin in raw_coins:
        value = raw_coin['value']

        is_confirmed = raw_coin['mintHeight'] >= 0  # always true
        if is_confirmed:
            confirmed += value
        else:
            unconfirmed += value

        balance += value

    return Balance(confirmed=confirmed, unconfirmed=unconfirmed, balance=balance)
