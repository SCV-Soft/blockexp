from datetime import datetime, timedelta
from typing import List, Optional, Union

from pymongo import DESCENDING

from .accessor import EthDaemonAccessor
from .mongo import EthMongoDatabase
from .web3 import AsyncWeb3
from ...error import BlockNotFound, TransactionNotFound
from ...model import Block, Transaction, DailyTransactions, CoinListing, TransactionId, EstimateFee, Wallet, Coin, \
    Balance, WalletAddress, Authhead, WalletCheckResult
from ...model.options import SteamingFindOptions
from ...types import Provider


class EthMongoProvider(Provider):
    def __init__(self, chain: str, network: str, db: EthMongoDatabase, accessor: EthDaemonAccessor):
        super().__init__(chain, network)
        self.db = db
        self.accessor = accessor

    @property
    def rpc(self) -> AsyncWeb3:
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
        raise NotImplementedError

    async def get_balance_for_address(self, address: str) -> Balance:
        value = await self.rpc.eth_getBalance(address, 'latest')
        return Balance(confirmed=value, unconfirmed=0, balance=value)

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
            block = await self.db.block_collection.fetch_one({'height': block_id})
        elif isinstance(block_id, str):
            block = await self.db.block_collection.fetch_one({'hash': block_id})
        else:
            raise TypeError

        if block is None:
            raise BlockNotFound(block_id)

        return block

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
        raise NotImplementedError

    async def create_wallet(self,
                            name: str,
                            pub_key: str,
                            path: Optional[str],
                            single_address: Optional[bool]) -> Wallet:
        raise NotImplementedError

    async def wallet_check(self, wallet: Wallet) -> WalletCheckResult:
        raise NotImplementedError

    async def stream_missing_wallet_addresses(self, wallet: Wallet):
        raise NotImplementedError

    async def stream_wallet_addresses(self, wallet: Wallet, limit: int) -> List[WalletAddress]:
        raise NotImplementedError

    async def update_wallet(self, wallet: Wallet, addresses: List[str]):
        raise NotImplementedError

    async def stream_wallet_transactions(self,
                                         wallet: Wallet,
                                         start_block: int = None,
                                         end_block: int = None,
                                         start_date: str = None,
                                         end_date: str = None,
                                         *,
                                         find_options: SteamingFindOptions) -> List[Transaction]:
        raise NotImplementedError

    async def get_wallet_balance(self, wallet: Wallet) -> Balance:
        raise NotImplementedError

    async def get_wallet_balance_at_time(self, wallet: Wallet, time: str) -> Balance:
        raise NotImplementedError

    async def stream_wallet_utxos(self,
                                  wallet: Wallet,
                                  limit: int = None,
                                  include_spent: bool = False) -> List[Coin]:
        raise NotImplementedError

    async def get_wallet(self, pub_key: str) -> Wallet:
        raise NotImplementedError

    async def get_fee(self, target: int) -> EstimateFee:
        return await self.accessor.get_fee(target)

    async def broadcast_transaction(self, raw_tx: str) -> TransactionId:
        raise NotImplementedError
        return TransactionId(txid)

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        tx = await self.get_transaction(tx_id)
        input_coin = Coin(
            chain=self.chain,
            network=self.network,
            mintTxid=tx.txid,
            mintIndex=0,
            mintHeight=tx.blockHeight,
            coinbase=False,
            value=tx.value,
            script="",
            address=tx.address,
            addresses=tx.addresses,
            spentTxid=tx.txid,
            spentHeight=tx.blockHeight,
            confirmations=0,
            wallets=tx.wallets,
        )

        output_coin = Coin(
            chain=self.chain,
            network=self.network,
            mintTxid=tx.txid,
            mintIndex=0,
            mintHeight=tx.blockHeight,
            coinbase=False,
            value=tx.value,
            script="",
            address=tx.address,
            addresses=tx.addresses,
            spentTxid=None,
            spentHeight=-1,
            confirmations=0,
            wallets=tx.wallets,
        )

        return CoinListing(
            inputs=[input_coin],
            outputs=[output_coin],
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
