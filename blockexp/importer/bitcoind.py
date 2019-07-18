import asyncio
import traceback
from collections import defaultdict
from enum import Enum
from typing import Union, List, Optional

from pymongo import UpdateOne, DESCENDING

from ..application import Application
from ..ext.database import MongoCollection, bulk_write_for, connect_database_for
from ..importer.base import Importer
from ..model import Block
from ..provider.bitcoind import BitcoinDaemonProvider, BtcBlock, BtcTransaction, BtcVOut, BtcScriptPubKey, BtcVIn, \
    BtcVInCoinbase
from ..proxy.jsonrpc import JSONRPCError
from ..utils import asrow
from ..utils.bitcoin import value2amount


class BtcTxOutputType(str, Enum):
    nonstandard = "nonstandard"
    pubkey = "pubkey"
    pubkeyhash = "pubkeyhash"
    scripthash = "scripthash"
    multisig = "multisig"
    nulldata = "nulldata"
    witness_v0_keyhash = "witness_v0_keyhash"
    witness_v0_scripthash = "witness_v0_scripthash"
    witness_unknown = "witness_unknown"


class BitcoinDaemonImporter(Importer):
    def __init__(self, chain: str, network: str, provider: BitcoinDaemonProvider, app: Application):
        super().__init__(chain, network)
        self.provider = provider
        self.app = app

    @property
    def _collection_key(self) -> str:
        return f'{self.provider.chain}:{self.provider.network}'

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

    async def run(self):
        while True:
            try:
                await self.worker()
            except Exception:
                traceback.print_exc()
                raise
            else:
                break

    async def worker(self):
        async with connect_database_for(self.app) as self.database:
            await self.task_create_indexes()
            await self.task_full_sync()

            while True:
                await self.task_progress_sync()
                await asyncio.sleep(30)

    async def task_create_indexes(self):
        def index(**data):
            return list(data.items())

        # block
        await self.block_collection.create_index(index(hash=1), background=True)
        await self.block_collection.create_index(index(processed=1, height=-1), background=True)
        await self.block_collection.create_index(index(timeNormalized=1), background=True)
        await self.block_collection.create_index(index(previousBlockHash=1), background=True)

        # coins
        await self.coin_collection.create_index(index(address=1), background=True)
        await self.coin_collection.create_index(index(mintHeight=1), background=True)
        await self.coin_collection.create_index(index(spentTxid=1), background=True)
        await self.coin_collection.create_index(index(spentHeight=1), background=True)
        await self.coin_collection.create_index(index(mintTxid=1, mintIndex=1), background=True)
        await self.coin_collection.create_index(index(wallets=1), background=True)
        await self.coin_collection.create_index(index(wallets=1, spentHeight=1, value=1, mintHeight=1), background=True)
        await self.coin_collection.create_index(index(wallets=1, spentTxid=1), background=True)
        await self.coin_collection.create_index(index(wallets=1, mintTxid=1), background=True)

        # transactions
        await self.tx_collection.create_index(index(txid=1), background=True)
        await self.tx_collection.create_index(index(blockHeight=1), background=True)
        await self.tx_collection.create_index(index(blockHash=1), background=True)
        await self.tx_collection.create_index(index(blockTimeNormalized=1), background=True)
        await self.tx_collection.create_index(index(wallets=1, blockTimeNormalized=1), background=True)
        await self.tx_collection.create_index(index(wallets=1, blockHeight=1), background=True)

        # wallets
        await self.wallet_collection.create_index(index(pubKey=1), background=True)

        # walletaddresses
        await self.wallet_address_collection.create_index(index(address=1, wallet=1), background=True, unique=True)
        await self.wallet_address_collection.create_index(index(wallet=1, address=1), background=True, unique=True)

    async def task_full_sync(self):
        db_tip = await self.get_db_tip()
        if db_tip is not None:
            return

        local_tip = await self.get_local_tip()
        for height in range(local_tip.height + 1):
            await self.import_block(height)

    async def task_progress_sync(self):
        db_tip = await self.get_db_tip()

        # TODO: store state in mongodb (detect full sync)
        assert db_tip is not None, 'full sync missing'

        height = db_tip.height
        invalid = False
        offset = 0
        while True:
            local_block = await self.get_local_block(height + offset)
            db_block = await self.get_db_block(height + offset)
            if db_block is not None and local_block is not None and local_block.hash == db_block.hash:
                break

            invalid = True
            offset -= 1

        if invalid:
            await self.undo_block(height + offset)

        db_tip = await self.get_db_tip()
        local_tip = await self.get_local_tip()

        for height in range(db_tip.height + 1, local_tip.height + 1):
            await self.import_block(height)

    async def get_db_block(self, block_height: int) -> Optional[Block]:
        block: Optional[dict] = await self.block_collection.find_one({'height': block_height})
        if block is None:
            return None

        return Block(**block, chain=self.chain, network=self.network)

    async def get_db_tip(self) -> Optional[Block]:
        block: Optional[dict] = await self.block_collection.find_one(sort=[('height', DESCENDING)])
        if block is None:
            return None

        return Block(**block, chain=self.chain, network=self.network)

    async def get_local_block(self, block_height: int) -> Optional[Block]:
        try:
            return await self.provider.get_block(block_height)
        except JSONRPCError as e:
            if e.code == -8:
                return None

            raise

    async def get_local_tip(self) -> Block:
        return await self.provider.get_local_tip()
        # return await self.get_local_block(1200)

    async def undo_block(self, height: int):
        print(self.chain, self.network, 'undo block', height)

        await self.block_collection.delete_many(
            {'height': {'$gte': height}}
        )

        await self.coin_collection.delete_many(
            {'mintHeight': {'$gte': height}}
        )

        await self.coin_collection.update_many(
            {'spentHeight': {'$gte': height}},
            {'$set':
                {
                    'spentHeight': -2,
                    'spentTxid': None,
                }
            }
        )

        await self.tx_collection.delete_many(
            {'blockHeight': {'$gte': height}}
        )

    async def import_block(self, height: int):
        print(self.chain, self.network, 'processing', height, 'block')
        raw_block: BtcBlock = await self.provider.get_raw_block(height)

        mint_ops = self.get_mint_ops(height, raw_block.tx)
        spend_ops = self.get_spend_ops(height, raw_block.tx, mint_ops)

        await self.write_mint_ops(mint_ops)
        await self.write_spend_ops(spend_ops)
        await self.write_txs(raw_block, raw_block.tx)
        await self.write_block(raw_block)

    async def write_block(self, raw_block: BtcBlock):
        block: Block = self.provider.convert_raw_block(raw_block)

        async with bulk_write_for(self.block_collection, ordered=False) as db_ops:
            db_ops.append(UpdateOne(
                filter={'hash': block.hash},
                update={
                    '$set': asrow(block),
                },
                upsert=True,
            ))

            db_ops.append(UpdateOne(
                filter={
                    'hash': block.previousBlockHash,
                },
                update={
                    '$set': {
                        'nextBlockHash': block.hash,
                    }
                },
            ))

    async def write_txs(self, raw_block: BtcBlock, txs: List[BtcTransaction]):
        async with bulk_write_for(self.tx_collection, ordered=False) as db_ops:
            for raw_tx in txs:
                tx = self.provider.convert_raw_transaction(raw_tx, raw_block)

                db_ops.append(UpdateOne(
                    filter={
                        'txid': tx.txid,
                    },
                    update={
                        '$set': asrow(tx),
                    },
                    upsert=True,
                ))

    def get_mint_ops(self, height: int, txs: List[BtcTransaction]) -> List[dict]:
        mint_ops = []

        for tx in txs:  # type: BtcTransaction
            is_coinbase = len(tx.vin) == 1 and isinstance(tx.vin[0], BtcVInCoinbase)

            for idx, vout in enumerate(tx.vout):  # type: int, BtcVOut
                spk: BtcScriptPubKey = vout.scriptPubKey
                amount = value2amount(vout.value)

                addresses = vout.scriptPubKey.addresses or []
                address = addresses[0] if addresses else None

                mint_ops.append({
                    'mintTxid': tx.txid,
                    'mintIndex': idx,
                    'mintHeight': height,
                    'coinbase': is_coinbase,
                    'value': amount,
                    'script': spk.hex,
                    'address': address,
                    'addresses': addresses,
                    'wallets': [],
                })

        return mint_ops

    async def write_mint_ops(self, mint_ops: List[dict]):
        async with bulk_write_for(self.coin_collection, ordered=False) as db_ops:
            for mint_op in mint_ops:
                if 'spentHeight' in mint_op:
                    update = {
                        '$set': mint_op,
                    }
                else:
                    update = {
                        '$set': mint_op,
                        '$setOnInsert': {
                            'spentHeight': -2,
                        }
                    }

                db_ops.append(UpdateOne(
                    filter={
                        'mintTxid': mint_op['mintTxid'],
                        'mintIndex': mint_op['mintIndex'],
                    },
                    update=update,
                    upsert=True,
                ))

    def get_spend_ops(self, height: int, txs: List[BtcTransaction], mint_ops: List[dict]) -> List[dict]:
        spend_ops = []

        mint_map = defaultdict(dict)
        for mint_op in mint_ops:
            mint_map[mint_op['mintTxid']][mint_op['mintIndex']] = mint_op

        for raw_tx in txs:  # type: BtcTransaction
            is_coinbase = len(raw_tx.vin) == 1 and isinstance(raw_tx.vin[0], BtcVInCoinbase)
            if is_coinbase:
                continue

            for idx, vin in enumerate(raw_tx.vin):  # type: int, Union[BtcVIn, BtcVInCoinbase]
                if isinstance(vin, BtcVInCoinbase):
                    continue

                same_block_spend = mint_map.get(vin.txid, {}).get(vin.vout)
                if same_block_spend is not None:
                    same_block_spend['spentTxid'] = raw_tx.txid
                    same_block_spend['spentHeight'] = height
                    continue

                spend_ops.append({
                    'mintTxid': vin.txid,
                    'mintIndex': vin.vout,
                    'spentTxid': raw_tx.txid,
                    'spentHeight': height,
                })

        return spend_ops

    async def write_spend_ops(self, spend_ops: List[dict]):
        async with bulk_write_for(self.coin_collection, ordered=False) as db_ops:
            for spend_op in spend_ops:
                db_ops.append(UpdateOne(
                    filter={
                        'mintTxid': spend_op['mintTxid'],
                        'mintIndex': spend_op['mintIndex'],
                    },
                    update={
                        '$set': {
                            'spentTxid': spend_op['spentTxid'],
                            'spentHeight': spend_op['spentHeight'],
                        },
                    },
                ))
