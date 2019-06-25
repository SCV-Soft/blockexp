from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...provider import Provider

api = Router()


@dataclass
class TransactionApiPath(ApiPath):
    tx_id: str


@dataclass
class TxIndexApiQuery:
    blockHeight: int
    blockHash: str
    limit: int
    since: str
    direction: str
    paging: str


@api.route('/', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_transactions(request: Request, path: ApiPath, query: TxIndexApiQuery, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{tx_id}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_transaction(request: Request, path: TransactionApiPath, provider: Provider) -> str:
    # TODO: get_local_tip
    raise NotImplementedError


@api.route('/{tx_id}/authhead', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_authhead(request: Request, path: TransactionApiPath, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{tx_id}/coins', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_coins_for_tx(request: Request, path: TransactionApiPath, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/send', methods=['POST'])
@typed_endpoint(tags=["bitcore"])
async def broadcast_transaction(request: Request, path: ApiPath, provider: Provider) -> str:
    raise NotImplementedError
