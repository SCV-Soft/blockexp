from dataclasses import dataclass
from enum import IntEnum
from typing import Union, Any, TypeVar, Generic

from bson import ObjectId

from ..model import Block

T = TypeVar('T')


class Direction(IntEnum):
    ASCENDING = 1
    DESCENDING = -1


@dataclass
class SteamingFindOptions(Generic[T]):
    paging: T
    since: ObjectId
    sort: Any
    direction: Direction
    limit: int


@dataclass(init=False)
class Provider:
    chain: str
    network: str

    def __init__(self, chain: str, network: str):
        self.chain = chain
        self.network = network

    async def stream_address_transactions(self):
        raise NotImplementedError

    async def get_balance_for_address(self):
        raise NotImplementedError

    async def get_blocks(self,
                         block_id: str = None,
                         since_block: Union[int, str] = None,
                         find_options: SteamingFindOptions[Block] = None):
        raise NotImplementedError

    async def get_block(self,
                        block_id: str = None) -> Block:
        raise NotImplementedError

    async def stream_transactions(self):
        raise NotImplementedError

    async def get_transaction(self):
        raise NotImplementedError

    async def get_authhead(self):
        raise NotImplementedError

    async def create_wallet(self):
        raise NotImplementedError

    async def wallet_check(self):
        raise NotImplementedError

    async def stream_missing_wallet_addresses(self):
        raise NotImplementedError

    async def update_wallet(self):
        raise NotImplementedError

    async def stream_wallet_transactions(self):
        raise NotImplementedError

    async def get_wallet_balance(self):
        raise NotImplementedError

    async def get_wallet_balance_at_time(self):
        raise NotImplementedError

    async def stream_wallet_utxos(self):
        raise NotImplementedError

    async def get_fee(self):
        raise NotImplementedError

    async def broadcast_transaction(self):
        raise NotImplementedError

    async def get_coins_for_tx(self):
        raise NotImplementedError

    async def get_daily_transactions(self):
        raise NotImplementedError

    async def get_local_tip(self):
        raise NotImplementedError

    async def get_locator_hashes(self):
        raise NotImplementedError
