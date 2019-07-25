from ...database import MongoDatabase, MongoCollection
from ...types import Base


def index(**data):
    return list(data.items())


class BtcMongoDatabase(Base):
    def __init__(self, chain: str, network: str, database: MongoDatabase):
        super().__init__(chain, network)
        self.database = database

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

    async def create_indexes(self):
        # block
        await self.block_collection.create_index(index(hash=1), background=True)
        await self.block_collection.create_index(index(processed=1, height=-1), background=True)
        await self.block_collection.create_index(index(timeNormalized=1), background=True)
        await self.block_collection.create_index(index(previousBlockHash=1), background=True)

        # coins
        await self.coin_collection.create_index(index(mintHeight=1), background=True)
        await self.coin_collection.create_index(index(spentTxid=1), background=True)
        await self.coin_collection.create_index(index(spentHeight=1), background=True)
        await self.coin_collection.create_index(index(mintTxid=1, mintIndex=1), background=True)
        await self.coin_collection.create_index(index(wallets=1), background=True)
        await self.coin_collection.create_index(index(wallets=1, spentHeight=1, value=1, mintHeight=1), background=True)
        await self.coin_collection.create_index(index(wallets=1, spentTxid=1), background=True)
        await self.coin_collection.create_index(index(wallets=1, mintTxid=1), background=True)
        await self.coin_collection.create_index(index(addresses=1), background=True)

        # transactions
        await self.tx_collection.create_index(index(txid=1), background=True)
        await self.tx_collection.create_index(index(blockHeight=1), background=True)
        await self.tx_collection.create_index(index(blockHash=1), background=True)
        await self.tx_collection.create_index(index(blockTimeNormalized=1), background=True)
        await self.tx_collection.create_index(index(wallets=1, blockTimeNormalized=1), background=True)
        await self.tx_collection.create_index(index(wallets=1, blockHeight=1), background=True)
        await self.tx_collection.create_index(index(addresses=1), background=True)

        # wallets
        await self.wallet_collection.create_index(index(pubKey=1), background=True)

        # walletaddresses
        await self.wallet_address_collection.create_index(index(address=1, wallet=1), background=True, unique=True)
        await self.wallet_address_collection.create_index(index(wallet=1, address=1), background=True, unique=True)
