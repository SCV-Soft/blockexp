import asyncio
import traceback
from datetime import datetime, timedelta
from typing import List, Optional

from pymongo import UpdateOne, DESCENDING

from .accessor import EthDaemonAccessor
from .mongo import EthMongoDatabase
from .types import EthBlock, EthTransaction
from ...application import Application
from ...database import bulk_write_for, connect_database_for
from ...model import Block
from ...types import Importer
from ...utils import asrow
from ...utils.jsonrpc import JSONRPCError


class EthDaemonImporter(Importer):
    db: EthMongoDatabase

    def __init__(self, chain: str, network: str, accessor: EthDaemonAccessor, app: Application):
        super().__init__(chain, network)
        self.accessor = accessor
        self.app = app

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
        async with connect_database_for(self.app) as database:
            self.db = EthMongoDatabase(self.chain, self.network, database)

            await self.task_full_sync()

            while True:
                await self.task_progress_sync()
                await asyncio.sleep(5)

    async def task_full_sync(self):
        db_tip = await self.get_db_tip()
        if db_tip is not None:
            return

        base_dt = datetime.utcnow() - timedelta(days=1)

        local_tip = await self.get_local_tip()
        height = local_tip.height

        for height in range(local_tip.height, 0, -1000):
            print(self.chain, self.network, 'peek', height, 'block')
            block = await self.get_local_block(height)
            if block.time < base_dt:
                break

        for height in range(height, local_tip.height):
            await self.import_block(height)

    async def task_progress_sync(self):
        db_tip: Optional[Block] = await self.get_db_tip()
        assert db_tip is not None, 'full sync missing'

        local_tip = await self.get_local_tip()

        for height in range(db_tip.height + 1, local_tip.height + 1):
            await self.import_block(height)

    async def get_db_block(self, block_height: int) -> Optional[Block]:
        block: Optional[dict] = await self.db.block_collection.find_one({'height': block_height})
        if block is None:
            return None

        return Block(**block, chain=self.chain, network=self.network)

    async def get_db_tip(self) -> Optional[Block]:
        block: Optional[dict] = await self.db.block_collection.find_one(sort=[('height', DESCENDING)])
        if block is None:
            return None

        return Block(**block, chain=self.chain, network=self.network)

    async def get_local_block(self, block_height: int) -> Optional[Block]:
        try:
            return await self.accessor.get_block(block_height)
        except JSONRPCError as e:
            raise

    async def get_local_tip(self) -> Block:
        return await self.accessor.get_local_tip()

    async def undo_block(self, height: int):
        print(self.chain, self.network, 'undo block', height)

        await self.db.block_collection.delete_many(
            {'height': {'$gte': height}}
        )

        await self.db.tx_collection.delete_many(
            {'blockHeight': {'$gte': height}}
        )

    async def import_block(self, height: int):
        print(self.chain, self.network, 'processing', height, 'block')
        raw_block: EthBlock = await self.accessor.get_raw_block(height)

        await self.write_txs(raw_block, raw_block.transactions)
        await self.write_block(raw_block)

    async def write_block(self, raw_block: EthBlock):
        block: Block = self.accessor.convert_raw_block(raw_block)

        async with bulk_write_for(self.db.block_collection, ordered=False) as db_ops:
            assert isinstance(block.nonce, int)
            row = asrow(block)
            row['nonce'] = repr(row['nonce'])

            db_ops.append(UpdateOne(
                filter={'hash': block.hash},
                update={
                    '$set': row,
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

    async def write_txs(self, raw_block: EthBlock, txs: List[EthTransaction]):
        async with bulk_write_for(self.db.tx_collection, ordered=False) as db_ops:
            for raw_tx in txs:
                tx = self.accessor.convert_raw_transaction(raw_tx, raw_block)
                assert isinstance(tx.value, int)
                row = asrow(tx)
                row['value'] = repr(row['value'])

                db_ops.append(UpdateOne(
                    filter={
                        'txid': tx.txid,
                    },
                    update={
                        '$set': row,
                    },
                    upsert=True,
                ))
