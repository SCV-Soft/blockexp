from typing import Union

from .base import Provider, SteamingFindOptions
from ..model import Block, BlockSchema
from ..proxy.bitcore import AsyncBitcore


class BitcoreProvider(Provider):
    def __init__(self, chain: str, network: str):
        super().__init__(chain, network)
        self.api = AsyncBitcore(chain, network)

    async def stream_address_transactions(self):
        pass

    async def get_balance_for_address(self):
        pass

    async def get_blocks(self, block_id: str = None, since_block: Union[int, str] = None,
                         find_options: SteamingFindOptions[Block] = None):
        pass

    async def get_block(self, block_id: str = None) -> Block:
        res = await self.api.get(f"block/{block_id}")
        res.raise_for_status()
        block = BlockSchema.load(res.json())
        return block

    async def stream_transactions(self):
        pass

    async def get_transaction(self):
        pass

    async def get_authhead(self):
        pass

    async def create_wallet(self):
        pass

    async def wallet_check(self):
        pass

    async def stream_missing_wallet_addresses(self):
        pass

    async def update_wallet(self):
        pass

    async def stream_wallet_transactions(self):
        pass

    async def get_wallet_balance(self):
        pass

    async def get_wallet_balance_at_time(self):
        pass

    async def stream_wallet_utxos(self):
        pass

    async def get_fee(self):
        pass

    async def broadcast_transaction(self):
        pass

    async def get_coins_for_tx(self):
        pass

    async def get_daily_transactions(self):
        pass

    async def get_local_tip(self):
        pass

    async def get_locator_hashes(self):
        pass
