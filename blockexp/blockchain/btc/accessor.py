from datetime import datetime
from typing import Union, Any

from .bitcoind import AsyncBitcoinDeamon
from .types import BtcTransaction, BtcBlock
from ...error import BlockNotFound, TransactionNotFound
from ...model import Block, Transaction, EstimateFee
from ...types import Accessor
from ...utils.jsonrpc import JSONRPCError


class BtcDaemonAccessor(Accessor):
    def __init__(self, chain: str, network: str, url: str):
        super().__init__(chain, network)
        self.rpc = AsyncBitcoinDeamon(url)
        self.is_legacy_getblock = None

    async def connect(self):
        await self.rpc.connect()

    async def close(self):
        await self.rpc.close()

    def _convert_raw_transaction(self, raw_transaction: dict) -> BtcTransaction:
        return BtcTransaction(**raw_transaction, _raw=raw_transaction)

    def _convert_raw_block(self, raw_block: dict) -> BtcBlock:
        return BtcBlock(**raw_block, _raw=raw_block)

    def _cast_block(self, block: BtcBlock) -> Block:
        assert len(block.tx) == block.nTx
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
            transactionCount=block.nTx,
            size=block.size,
            bits=int(block.bits, 16),
            reward=None,
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

    async def _detect_legacy_getblock(self, *, verbosity: int):
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
                    return True
            else:
                return False

    async def _get_block(self, block_id: Union[str, int], *, verbosity: int) -> BtcBlock:
        if isinstance(block_id, int):
            block_hash = await self.get_block_hash(block_id)
        else:
            block_hash = block_id

        if self.is_legacy_getblock is None:
            self.is_legacy_getblock = await self._detect_legacy_getblock(verbosity=verbosity)

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

    def convert_raw_block(self, raw_block: Any) -> Block:
        assert isinstance(raw_block, BtcBlock)
        return self._cast_block(raw_block)

    def convert_raw_transaction(self, raw_transaction: Any, raw_block: Any) -> Transaction:
        assert isinstance(raw_transaction, BtcTransaction)
        assert isinstance(raw_block, BtcBlock)
        return self._cast_transaction(raw_transaction, raw_block)

    async def get_block(self, block_id: Union[str, int]) -> Block:
        block = await self._get_block(block_id, verbosity=1)
        return self._cast_block(block)

    async def get_block_hash(self, block_height: int) -> str:
        try:
            return await self.rpc.getblockhash(block_height)
        except JSONRPCError as e:
            if e.code == -8 and e.message == "Block height out of range":
                raise BlockNotFound(repr(block_height)) from e

            raise

    async def get_raw_block(self, block_id: Union[str, int]) -> BtcBlock:
        return await self._get_block(block_id, verbosity=2)

    async def get_transaction(self, tx_id: str) -> Transaction:
        raw_transaction = await self.rpc.getrawtransaction(tx_id)
        assert isinstance(raw_transaction, dict)

        transaction = self._convert_raw_transaction(raw_transaction)
        block = await self.get_block(transaction.blockhash)
        return self._cast_transaction(transaction, block)

    async def get_local_tip(self) -> Block:
        block_hash = await self.rpc.getbestblockhash()
        return await self.get_block(block_hash)

    async def get_fee(self, target: int) -> EstimateFee:
        return EstimateFee(**(await self.rpc.estimatesmartfee(target)))
