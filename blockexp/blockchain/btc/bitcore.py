from typing import Union, List, Any, cast, Type, TypeVar
from urllib.parse import urljoin

import requests_async as requests
import typing_inspect
from requests import HTTPError
from requests_async import Response
from starlette.exceptions import HTTPException

from ...model import get_schema, Block, Transaction, CoinListing, Authhead, Balance, Coin, \
    EstimateFee, Wallet, WalletAddress, TransactionId
from ...model.options import SteamingFindOptions
from ...types import Provider


class AsyncBitcore:
    URL = "https://api.bitcore.io/api/{chain}/{network}/"

    def __init__(self, chain: str, network: str):
        self.url = self.URL.format(chain=chain, network=network)
        self.session = requests.Session()

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.session.__aexit__(exc_type, exc_val, exc_tb)

    def get_url(self, path: str) -> str:
        return urljoin(self.url, path)

    async def get(self, path: str, **kwargs):
        url = self.get_url(path)
        return await self.session.get(url, **kwargs)

    async def post(self, path: str, **kwargs):
        url = self.get_url(path)
        return await self.session.post(url, **kwargs)


T = TypeVar('T')


class BitcoreProvider(Provider):
    def __init__(self, chain: str, network: str):
        super().__init__(chain, network)
        self.api = AsyncBitcore(chain, network)

    async def __aenter__(self):
        await self.api.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.api.__aexit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def _raise_for_status(response: Response):
        try:
            response.raise_for_status()
        except HTTPError as e:  # type: HTTPError
            raise HTTPException(response.status_code)  # type: HTTPException

    async def _get(self, cls: Type[T], url, **kwargs) -> T:
        res = await self.api.get(url, **kwargs)
        self._raise_for_status(res)
        return self._load(cls, res)

    async def _post(self, cls: Type[T], url, **kwargs) -> T:
        res = await self.api.post(url, **kwargs)
        self._raise_for_status(res)
        return self._load(cls, res)

    @staticmethod
    def _load(cls: Type[T], res: Response) -> T:
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

    async def get_balance_for_address(self, address: str) -> Balance:
        return await self._get(Balance, f'address/{address}/balance')

    async def stream_blocks(self,
                            since_block: Union[str, int] = None,
                            start_date: str = None,
                            end_date: str = None,
                            date: str = None,
                            find_options: SteamingFindOptions = None) -> List[Block]:
        return await self._get(List[Block], f'block/', params={
            'sinceBlock': since_block,
            'startDate': start_date,
            'endDate': end_date,
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

    async def wallet_check(self, wallet: Wallet):
        return await self._get(Block, f'block/tip')

    async def stream_missing_wallet_addresses(self, wallet: Wallet) -> List[str]:
        pass

    async def stream_wallet_addresses(self, wallet: Wallet, limit: int) -> List[WalletAddress]:
        pass

    async def update_wallet(self, wallet: Wallet, addresses: List[str]):
        pass

    async def stream_wallet_transactions(self, wallet: Wallet, start_block: int = None, end_block: int = None,
                                         start_date: str = None, end_date: str = None, *,
                                         find_options: SteamingFindOptions) -> List[Transaction]:
        pass

    async def get_wallet_balance(self, wallet: Wallet) -> Balance:
        pass

    async def get_wallet_balance_at_time(self, wallet: Wallet, time: str) -> Balance:
        pass

    async def stream_wallet_utxos(self, wallet: Wallet, limit: int = None, include_spent: bool = False) -> List[Coin]:
        pass

    async def get_wallet(self, pub_key: str) -> Wallet:
        return Wallet(
            chain=self.chain,
            network=self.network,
            name=pub_key,
            pubKey=pub_key,
            singleAddress=None,
            path=None,
        )
