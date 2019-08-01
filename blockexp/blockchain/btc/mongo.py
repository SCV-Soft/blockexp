from typing import Optional

from pymongo import DESCENDING

from ..utils.mongo import BlockchainMongoCollection, BlockchainMongoDatabase, index
from ...database import MongoDatabase
from ...error import BlockNotFound
from ...model import Block, Transaction, Coin, Wallet, WalletAddress


class BtcMongoDatabase(BlockchainMongoDatabase):
    block_collection: BlockchainMongoCollection[Block]
    tx_collection: BlockchainMongoCollection[Transaction]
    coin_collection: BlockchainMongoCollection[Coin]
    wallet_collection: BlockchainMongoCollection[Wallet]
    wallet_address_collection: BlockchainMongoCollection[WalletAddress]

    def __init__(self, chain: str, network: str, database: MongoDatabase):
        super().__init__(chain, network, database)
        self.block_collection = self.new_collection('blocks', self.convert_raw_block, self.fetch_block_tip)
        self.tx_collection = self.new_collection('transactions', self.convert_raw_transaction, self.fetch_block_tip)
        self.coin_collection = self.new_collection('coins', self.convert_raw_coin, self.fetch_block_tip)
        self.wallet_collection = self.new_collection('wallets', self.convert_raw_wallet, self.fetch_block_tip)
        self.wallet_address_collection = self.new_collection('walletaddresses', self.convert_raw_wallet_address, None)

    async def create_indexes(self):
        # block
        await self.block_collection.create_index(index(hash=1), background=True)
        await self.block_collection.create_index(index(height=1), background=True)
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

    async def fetch_block_tip(self):
        raw_block: Optional[dict] = await self.block_collection.find_one(sort=[('height', DESCENDING)])
        if raw_block is None:
            raise BlockNotFound(None)

        return self.convert_raw_block(raw_block)
