from typing import Any, Union, Optional

from hexbytes import HexBytes

from .types import EthBlock, EthTransaction
from .web3 import AsyncWeb3
from ...model import Block, Transaction, EstimateFee
from ...types import Accessor


def as_hex(s: Optional[HexBytes]) -> Optional[str]:
    return s.hex() if s else None


class EthDaemonAccessor(Accessor):
    def __init__(self, chain: str, network: str, url: str):
        super().__init__(chain, network)
        self.rpc = AsyncWeb3(url)
        self.is_legacy_getblock = None

    def _cast_block(self, raw_block: EthBlock) -> Block:
        return Block(
            chain=self.chain,
            network=self.network,
            confirmations=None,
            height=raw_block.number,
            hash=raw_block.hash.hex(),
            version=-1,
            merkleRoot=as_hex(raw_block.transactionsRoot),
            time=raw_block.timestamp,
            timeNormalized=raw_block.timestamp,
            nonce=int(as_hex(raw_block.nonce), 16),
            previousBlockHash=as_hex(raw_block.parentHash),
            nextBlockHash=None,
            transactionCount=len(raw_block.transactions),
            size=raw_block.size,
            bits=-1,
            reward=None,
            processed=None,
        )

    def _cast_transaction(self, raw_transaction: EthTransaction, raw_block: EthBlock) -> Transaction:
        return Transaction(
            txid=as_hex(raw_transaction.hash),
            chain=self.chain,
            network=self.network,
            blockHeight=raw_block.number,
            blockHash=as_hex(raw_transaction.blockHash),
            blockTime=raw_block.timestamp.isoformat(),
            blockTimeNormalized=raw_block.timestamp.isoformat(),
            coinbase=False,  # TODO: ?
            fee=-1,
            size=-1,
            locktime=0,
            inputCount=1,
            outputCount=1,
            value=raw_transaction.value,
            confirmations=None,
            address=as_hex(raw_transaction.to),
            addresses=list(filter(None, [
                as_hex(raw_transaction.from_),
                as_hex(raw_transaction.to),
            ])),
            wallets=[],
        )

    @staticmethod
    def _convert_raw_transaction(raw_transaction: dict) -> EthTransaction:
        return EthTransaction.load(raw_transaction)

    @staticmethod
    def _convert_raw_block(raw_block: dict) -> EthBlock:
        return EthBlock.load(raw_block)

    def convert_raw_block(self, raw_block: Any) -> Block:
        assert isinstance(raw_block, EthBlock)
        return self._cast_block(raw_block)

    def convert_raw_transaction(self, raw_transaction: Any, raw_block: Any) -> Transaction:
        assert isinstance(raw_transaction, EthTransaction)
        assert isinstance(raw_block, EthBlock)
        return self._cast_transaction(raw_transaction, raw_block)

    async def _get_block(self, block_id: Union[str, int], *, with_transactions: bool) -> EthBlock:
        if isinstance(block_id, str):
            raw_block = await self.rpc.eth_getBlockByHash(block_id, with_transactions)
        elif isinstance(block_id, int):
            raw_block = await self.rpc.eth_getBlockByNumber(block_id, with_transactions)
        else:
            raise TypeError

        return self._convert_raw_block(raw_block)

    async def get_block(self, block_id: Union[str, int]) -> Block:
        raw_block = await self.get_raw_block(block_id)
        return self._cast_block(raw_block)

    async def get_raw_block(self, block_id: Union[str, int]) -> EthBlock:
        return await self._get_block(block_id, with_transactions=True)

    async def get_transaction(self, tx_id: str) -> Transaction:
        raw_transaction = await self.rpc.eth_getTransactionByHash(tx_id)
        assert isinstance(raw_transaction, dict)

        transaction = self._convert_raw_transaction(raw_transaction)
        raw_block = await self._get_block(transaction.blockHash.hex(), with_transactions=False)
        return self._cast_transaction(transaction, raw_block)

    async def get_local_tip(self) -> Block:
        block_id = await self.rpc.eth_blockNumber()
        raw_block = await self._get_block(block_id, with_transactions=False)
        return self._cast_block(raw_block)

    async def get_fee(self, target: int) -> EstimateFee:
        gas = await self.rpc.eth_estimateGas()
        return EstimateFee(feerate=gas, blocks=-1)
