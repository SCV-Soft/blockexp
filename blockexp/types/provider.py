from typing import Union, Any, TypeVar, List, Optional

from ._base import Base
from ..model import Block, Transaction, CoinListing, Authhead, TransactionId, Balance, EstimateFee, Wallet, Coin, \
    WalletAddress
from ..model import DailyTransactions
from ..model.options import SteamingFindOptions

T = TypeVar('T')


class Provider(Base):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def stream_address_transactions(self,
                                          address: str,
                                          unspent: bool,
                                          find_options: SteamingFindOptions) -> List[Transaction]:
        raise NotImplementedError

    async def stream_address_utxos(self, address: str, unspent: bool, find_options: SteamingFindOptions) -> List[Any]:
        raise NotImplementedError

    async def get_balance_for_address(self, address: str) -> Balance:
        raise NotImplementedError

    async def stream_blocks(self,
                            since_block: Union[str, int] = None,
                            start_date: str = None,
                            end_date: str = None,
                            date: str = None,
                            *,
                            find_options: SteamingFindOptions) -> List[Block]:
        raise NotImplementedError

    async def get_block(self, block_id: Union[str, int]) -> Block:
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

    async def create_wallet(self,
                            name: str,
                            pub_key: str,
                            path: Optional[str],
                            single_address: Optional[bool]) -> Wallet:
        raise NotImplementedError

    async def wallet_check(self, wallet: Wallet):
        raise NotImplementedError

    async def stream_missing_wallet_addresses(self, wallet: Wallet) -> List[str]:
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
        raise NotImplementedError

    async def broadcast_transaction(self, raw_tx: str) -> TransactionId:
        raise NotImplementedError

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        raise NotImplementedError

    async def get_daily_transactions(self) -> DailyTransactions:
        raise NotImplementedError

    async def get_local_tip(self) -> Block:
        raise NotImplementedError

    async def get_locator_hashes(self):
        raise NotImplementedError
