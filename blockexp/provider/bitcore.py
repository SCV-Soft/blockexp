import typing
from typing import Union, Type, TypeVar, cast, Any, List

import typing_inspect
from requests_async import Response

from blockexp.model import Authhead, TransactionId, AddressBalance, Coin, EstimateFee
from starlette_typed.marshmallow import build_schema, Schema
from .base import Provider, ProviderType
from blockexp.provider import SteamingFindOptions
from ..model import Block, Transaction, CoinListing
from ..proxy.bitcore import AsyncBitcore

T = TypeVar('T')

SCHEMAS = {}


def get_schema(cls: Type, *, many: bool) -> Schema:
    schema = SCHEMAS.get((cls, many))
    if schema is None:
        schema = SCHEMAS[(cls, many)] = build_schema(cls, many=many)

    return schema


class BitcoreProvider(Provider):
    def __init__(self, chain: str, network: str):
        super().__init__(chain, network)
        self.api = AsyncBitcore(chain, network)

    @property
    def type(self) -> ProviderType:
        return ProviderType.UTXO

    async def __aenter__(self):
        await self.api.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.api.__aexit__(exc_type, exc_val, exc_tb)

    async def _get(self, cls: Type[T], url, **kwargs) -> T:
        res = await self.api.get(url, **kwargs)
        res.raise_for_status()
        return await self._load(cls, res)

    async def _post(self, cls: Type[T], url, **kwargs) -> T:
        res = await self.api.post(url, **kwargs)
        res.raise_for_status()
        return await self._load(cls, res)

    @staticmethod
    async def _load(cls: Type[T], res: Response) -> T:
        if cls == Any:
            return res.json()
        else:
            if typing_inspect.get_origin(cls) == list:
                cls, = typing_inspect.get_args(cls)
                many = True
            else:
                many = False

            schema = get_schema(cls, many=many)
            obj = schema.load(res.json())
            return cast(T, obj)

    async def stream_address_transactions(self,
                                          address: str,
                                          unspent: bool,
                                          find_options: SteamingFindOptions) -> List[Transaction]:
        # TODO: same return with stream_address_utxos in bitcore [???]
        return await self._get(Any, f'address/{address}/txs', params={
            'unspent': unspent,
            'limit': find_options.limit,
            'since': find_options.since,
        })

    async def stream_address_utxos(self,
                                   address: str,
                                   unspent: bool,
                                   find_options: SteamingFindOptions) -> List[Coin]:
        return await self._get(List[Coin], f'address/{address}', params={
            'unspent': unspent,
            'limit': find_options.limit,
            'since': find_options.since,
        })

    async def get_balance_for_address(self, address: str) -> AddressBalance:
        return await self._get(AddressBalance, f'address/{address}/balance')

    async def stream_blocks(self,
                            since_block: Union[str, int] = None,
                            date: str = None,
                            find_options: SteamingFindOptions[Block] = None) -> List[Block]:
        return await self._get(List[Block], f'block/', params={
            'sinceBlock': since_block,
            'date': date,
            'limit': find_options.limit,
            'since': find_options.since,
            'direction': find_options.direction.value if find_options.direction is not None else None,
            'paging': find_options.paging,
        })

    async def get_block(self, block_id: Union[str, int]) -> Block:
        return await self._get(Block, f'block/{block_id}')

    async def stream_transactions(self,
                                  block_height: int,
                                  block_hash: str,
                                  find_options: SteamingFindOptions) -> List[Transaction]:
        return await self._get(List[Transaction], f'tx/', params={
            'blockHeight': block_height,
            'blockHash': block_hash,
            'limit': find_options.limit,
            'since': find_options.since,
            'direction': find_options.direction.value if find_options.direction is not None else None,
            'paging': find_options.paging,
        })

    async def get_transaction(self, tx_id: str) -> Transaction:
        return await self._get(Transaction, f'tx/{tx_id}')

    async def get_authhead(self, tx_id: str) -> Authhead:
        return await self._get(Authhead, f'tx/{tx_id}/authhead')

    async def create_wallet(self, name: str, pub_key: str, path: str, single_address: bool) -> Any:
        return await self._post(Any, f'wallet/', json={
            'name': name,
            'singleAddress': single_address,
            'pubKey': pub_key,
            'path': path,
        })

    async def wallet_check(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def stream_missing_wallet_addresses(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def update_wallet(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def stream_wallet_transactions(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def get_wallet_balance(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def get_wallet_balance_at_time(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def stream_wallet_utxos(self):
        # TODO: wallet auth
        raise NotImplementedError

    async def get_fee(self, target: int) -> EstimateFee:
        return await self._get(EstimateFee, f'fee/{target}')

    async def broadcast_transaction(self, raw_tx: Any) -> TransactionId:
        return await self._post(TransactionId, f'tx/send', json={
            'rawTx': raw_tx,
        })

    async def get_coins_for_tx(self, tx_id: str) -> CoinListing:
        return await self._get(CoinListing, f'tx/{tx_id}/coins')

    async def get_daily_transactions(self) -> Any:
        return await self._get(Any, f'stats/daily-transactions')

    async def get_local_tip(self) -> Block:
        return await self._get(Block, f'block/tip')

    async def get_locator_hashes(self):
        # missing api endpoint
        raise NotImplementedError
