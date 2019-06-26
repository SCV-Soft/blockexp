from dataclasses import dataclass
from enum import IntEnum
from typing import Union, Any, TypeVar, Generic, List

from bson import ObjectId

from ..model import Block, Transaction, CoinListing, Authhead, TransactionId, AddressBalance, EstimateFee

T = TypeVar('T')


class Direction(IntEnum):
    ASCENDING = 1
    DESCENDING = -1


@dataclass
class SteamingFindOptions(Generic[T]):
    paging: T = None
    since: str = None
    sort: Any = None
    direction: Direction = None
    limit: int = None


@dataclass(init=False)
class Provider:
    chain: str
    network: str

    def __init__(self, chain: str, network: str):
        self.chain = chain
        self.network = network

    async def stream_address_transactions(self,
                                          address: str,
                                          unspent: bool,
                                          find_options: SteamingFindOptions) -> List[Any]:
        raise NotImplementedError

    async def stream_address_utxos(self, address: str, unspent: bool, find_options: SteamingFindOptions) -> List[Any]:
        raise NotImplementedError

    async def get_balance_for_address(self, address: str) -> AddressBalance:
        raise NotImplementedError

    async def stream_blocks(self,
                            since_block: Union[int, str] = None,
                            date: str = None,
                            find_options: SteamingFindOptions[Block] = None) -> List[Block]:
        raise NotImplementedError

    async def get_block(self, block_id: str = None) -> Block:
        raise NotImplementedError

    async def stream_transactions(self,
                                  block_height: int,
                                  block_hash: str,
                                  find_options: SteamingFindOptions) -> List[Transaction]:
        raise NotImplementedError

    async def get_transaction(self, tx_id: str) -> Transaction:
        raise NotImplementedError

    async def get_authhead(self, tx_id: str) -> Authhead:
        raise NotImplementedError

    async def create_wallet(self, name: str, pub_key: str, path: str, single_address: bool) -> Any:
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

    async def get_fee(self, target: int) -> EstimateFee:
        raise NotImplementedError

    async def broadcast_transaction(self, raw_tx: Any) -> TransactionId:
        raise NotImplementedError

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        raise NotImplementedError

    async def get_daily_transactions(self) -> Any:
        raise NotImplementedError

    async def get_local_tip(self) -> Block:
        raise NotImplementedError

    async def get_locator_hashes(self):
        raise NotImplementedError
