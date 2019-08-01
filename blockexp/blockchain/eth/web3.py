from typing import Any

from ...utils.jsonrpc import AsyncJsonRPC


# noinspection PyPep8Naming
class AsyncWeb3(AsyncJsonRPC):
    async def web3_clientVersion(self) -> str:
        return await self.call("web3_clientVersion")

    async def web3_sha3(self, *args) -> Any:
        return await self.call('web3_sha3', *args)

    async def net_version(self, *args) -> Any:
        return await self.call('net_version', *args)

    async def net_peerCount(self, *args) -> Any:
        return await self.call('net_peerCount', *args)

    async def net_listening(self, *args) -> Any:
        return await self.call('net_listening', *args)

    async def eth_protocolVersion(self, *args) -> Any:
        return await self.call('eth_protocolVersion', *args)

    async def eth_syncing(self, *args) -> Any:
        return await self.call('eth_syncing', *args)

    async def eth_coinbase(self, *args) -> Any:
        return await self.call('eth_coinbase', *args)

    async def eth_mining(self, *args) -> Any:
        return await self.call('eth_mining', *args)

    async def eth_hashrate(self, *args) -> Any:
        return await self.call('eth_hashrate', *args)

    async def eth_gasPrice(self, *args) -> Any:
        return await self.call('eth_gasPrice', *args)

    async def eth_accounts(self, *args) -> Any:
        return await self.call('eth_accounts', *args)

    async def eth_blockNumber(self) -> int:
        block_number: str = await self.call("eth_blockNumber")
        return int(block_number, 16)

    async def eth_getBalance(self, *args) -> int:
        value = await self.call('eth_getBalance', *args)
        return int(value, 16)

    async def eth_getStorageAt(self, *args) -> Any:
        return await self.call('eth_getStorageAt', *args)

    async def eth_getTransactionCount(self, *args) -> Any:
        return await self.call('eth_getTransactionCount', *args)

    async def eth_getBlockTransactionCountByHash(self, *args) -> Any:
        return await self.call('eth_getBlockTransactionCountByHash', *args)

    async def eth_getBlockTransactionCountByNumber(self, *args) -> Any:
        return await self.call('eth_getBlockTransactionCountByNumber', *args)

    async def eth_getUncleCountByBlockHash(self, *args) -> Any:
        return await self.call('eth_getUncleCountByBlockHash', *args)

    async def eth_getUncleCountByBlockNumber(self, *args) -> Any:
        return await self.call('eth_getUncleCountByBlockNumber', *args)

    async def eth_getCode(self, *args) -> Any:
        return await self.call('eth_getCode', *args)

    async def eth_sign(self, *args) -> Any:
        return await self.call('eth_sign', *args)

    async def eth_sendTransaction(self, *args) -> Any:
        return await self.call('eth_sendTransaction', *args)

    async def eth_sendRawTransaction(self, *args) -> Any:
        return await self.call('eth_sendRawTransaction', *args)

    async def eth_call(self, *args) -> Any:
        return await self.call('eth_call', *args)

    async def eth_estimateGas(self, *args) -> int:
        gas: str = await self.call('eth_estimateGas', *args)
        assert isinstance(gas, str), gas
        return int(gas)

    async def eth_getBlockByHash(self, block_hash: str, full_transactions: bool = True) -> dict:
        return await self.call("eth_getBlockByHash", block_hash, full_transactions)

    async def eth_getBlockByNumber(self, block_number: int, full_transactions: bool = True) -> dict:
        return await self.call("eth_getBlockByNumber", hex(block_number), full_transactions)

    async def eth_getTransactionByHash(self, *args) -> Any:
        return await self.call('eth_getTransactionByHash', *args)

    async def eth_getTransactionByBlockHashAndIndex(self, *args) -> Any:
        return await self.call('eth_getTransactionByBlockHashAndIndex', *args)

    async def eth_getTransactionByBlockNumberAndIndex(self, *args) -> Any:
        return await self.call('eth_getTransactionByBlockNumberAndIndex', *args)

    async def eth_getTransactionReceipt(self, *args) -> Any:
        return await self.call('eth_getTransactionReceipt', *args)

    async def eth_getUncleByBlockHashAndIndex(self, *args) -> Any:
        return await self.call('eth_getUncleByBlockHashAndIndex', *args)

    async def eth_getUncleByBlockNumberAndIndex(self, *args) -> Any:
        return await self.call('eth_getUncleByBlockNumberAndIndex', *args)

    async def eth_getCompilers(self, *args) -> Any:
        return await self.call('eth_getCompilers', *args)

    async def eth_compile(self, *args) -> Any:
        return await self.call('eth_compile', *args)

    async def eth_compileSolidity(self, *args) -> Any:
        return await self.call('eth_compileSolidity', *args)

    async def eth_compileSerpent(self, *args) -> Any:
        return await self.call('eth_compileSerpent', *args)

    async def eth_newFilter(self, *args) -> Any:
        return await self.call('eth_newFilter', *args)

    async def eth_newBlockFilter(self, *args) -> Any:
        return await self.call('eth_newBlockFilter', *args)

    async def eth_newPendingTransactionFilter(self, *args) -> Any:
        return await self.call('eth_newPendingTransactionFilter', *args)

    async def eth_uninstallFilter(self, *args) -> Any:
        return await self.call('eth_uninstallFilter', *args)

    async def eth_getFilterChanges(self, *args) -> Any:
        return await self.call('eth_getFilterChanges', *args)

    async def eth_getFilterLogs(self, *args) -> Any:
        return await self.call('eth_getFilterLogs', *args)

    async def eth_getLogs(self, *args) -> Any:
        return await self.call('eth_getLogs', *args)

    async def eth_getWork(self, *args) -> Any:
        return await self.call('eth_getWork', *args)

    async def eth_submitWork(self, *args) -> Any:
        return await self.call('eth_submitWork', *args)

    async def eth_submitHashrate(self, *args) -> Any:
        return await self.call('eth_submitHashrate', *args)

    async def db_putString(self, *args) -> Any:
        return await self.call('db_putString', *args)

    async def db_getString(self, *args) -> Any:
        return await self.call('db_getString', *args)

    async def db_putHex(self, *args) -> Any:
        return await self.call('db_putHex', *args)

    async def db_getHex(self, *args) -> Any:
        return await self.call('db_getHex', *args)

    async def shh_post(self, *args) -> Any:
        return await self.call('shh_post', *args)

    async def shh_version(self, *args) -> Any:
        return await self.call('shh_version', *args)

    async def shh_newIdentity(self, *args) -> Any:
        return await self.call('shh_newIdentity', *args)

    async def shh_hasIdentity(self, *args) -> Any:
        return await self.call('shh_hasIdentity', *args)

    async def shh_newGroup(self, *args) -> Any:
        return await self.call('shh_newGroup', *args)

    async def shh_addToGroup(self, *args) -> Any:
        return await self.call('shh_addToGroup', *args)

    async def shh_newFilter(self, *args) -> Any:
        return await self.call('shh_newFilter', *args)

    async def shh_uninstallFilter(self, *args) -> Any:
        return await self.call('shh_uninstallFilter', *args)

    async def shh_getFilterChanges(self, *args) -> Any:
        return await self.call('shh_getFilterChanges', *args)

    async def shh_getMessages(self, *args) -> Any:
        return await self.call('shh_getMessages', *args)
