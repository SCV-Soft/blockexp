from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath

api = Router()


@dataclass
class AddressApiPath(ApiPath):
    address: str


@dataclass
class AddressApiQuery:
    unspent: str
    since: str
    limit: int = 10


@api.route('/{address}/txs', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_address_transactions(request: Request, path: AddressApiPath, query: AddressApiQuery) -> str:
    raise NotImplementedError


@api.route('/{address}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_address_utxos(request: Request, path: AddressApiPath, query: AddressApiQuery) -> str:
    raise NotImplementedError


@api.route('/{address}/balance', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_balance_for_address(request: Request, path: AddressApiPath) -> str:
    raise NotImplementedError
