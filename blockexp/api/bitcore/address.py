from dataclasses import dataclass
from typing import List

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...model import Balance, Coin
from ...model.options import SteamingFindOptions
from ...types import Provider

api = Router()


@dataclass
class AddressApiPath(ApiPath):
    address: str


@dataclass
class AddressApiQuery:
    unspent: bool = None
    since: int = None
    limit: int = None


@api.route('/{address}/txs', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_address_transactions(request: Request, path: AddressApiPath, query: AddressApiQuery,
                                      provider: Provider) -> List[Coin]:
    return await provider.stream_address_utxos(
        address=path.address,
        unspent=query.unspent,
        find_options=SteamingFindOptions(
            since=query.since,
            limit=query.limit,
        )
    )


@api.route('/{address}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_address_utxos(request: Request, path: AddressApiPath, query: AddressApiQuery,
                               provider: Provider) -> List[Coin]:
    return await provider.stream_address_utxos(
        address=path.address,
        unspent=query.unspent,
        find_options=SteamingFindOptions(
            since=query.since,
            limit=query.limit,
        )
    )


@api.route('/{address}/balance', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_balance_for_address(request: Request, path: AddressApiPath, provider: Provider) -> Balance:
    return await provider.get_balance_for_address(path.address)
