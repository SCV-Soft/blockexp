from dataclasses import dataclass
from typing import List

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...model import Transaction, CoinListing, Authhead, TransactionId
from ...provider import Provider
from ...provider.base import SteamingFindOptions, Direction

api = Router()


@dataclass
class TransactionApiPath(ApiPath):
    tx_id: str


@dataclass
class TxIndexApiQuery:
    blockHeight: int = None
    blockHash: str = None
    limit: int = None
    since: str = None
    direction: Direction = None
    paging: str = None


@api.route('/', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_transactions(request: Request, path: ApiPath, query: TxIndexApiQuery, provider: Provider) -> List[
    Transaction]:
    return await provider.stream_transactions(
        block_height=query.blockHeight,
        block_hash=query.blockHash,
        find_options=SteamingFindOptions(
            limit=query.limit,
            since=query.since,
            direction=query.direction,
            paging=query.paging,
        )
    )


@api.route('/{tx_id}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_transaction(request: Request, path: TransactionApiPath, provider: Provider) -> Transaction:
    return await provider.get_transaction(path.tx_id)


@api.route('/{tx_id}/authhead', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_authhead(request: Request, path: TransactionApiPath, provider: Provider) -> Authhead:
    return await provider.get_authhead(path.tx_id)


@api.route('/{tx_id}/coins', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_coins_for_tx(request: Request, path: TransactionApiPath, provider: Provider) -> CoinListing:
    return await provider.get_coins_for_tx(path.tx_id)


@dataclass
class BroadcastTransactionRequest:
    chain: str
    network: str
    rawTx: str


@api.route('/send', methods=['POST'])
@typed_endpoint(tags=["bitcore"])
async def broadcast_transaction(request: Request, path: ApiPath, provider: Provider,
                                body: BroadcastTransactionRequest) -> TransactionId:
    return await provider.broadcast_transaction(body.rawTx)
