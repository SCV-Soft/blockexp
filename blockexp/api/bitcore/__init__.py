from contextlib import asynccontextmanager
from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed.endpoint import register_handler
from ...blockchain import get_blockchain
from ...database import connect_database, MongoDatabase
from ...types import Blockchain, Provider, Accessor


@dataclass
class ApiPath:
    chain: str
    network: str


def get_blockchain_from_request(request: Request) -> Blockchain:
    path_params = request.path_params
    chain = path_params['chain']
    network = path_params['network']

    blockchain = get_blockchain(chain, network, request.app)
    if blockchain is None:
        raise NotImplementedError((chain, network))

    return blockchain


@register_handler
@asynccontextmanager
async def provider(request: Request) -> Provider:
    blockchain = get_blockchain_from_request(request)
    async with connect_database(request) as database:
        # noinspection PyShadowingNames
        async with blockchain.get_provider(database) as provider:
            yield provider


@register_handler
@asynccontextmanager
async def accessor(request: Request) -> Accessor:
    blockchain = get_blockchain_from_request(request)
    # noinspection PyShadowingNames
    async with blockchain.get_accessor() as accessor:
        yield accessor


def build_api() -> Router:
    from . import address, block, fee, stats, tx, wallet, status

    # noinspection PyShadowingNames
    api = Router()
    api.mount('/{chain}/{network}/address', address.api)
    api.mount('/{chain}/{network}/block', block.api)
    api.mount('/{chain}/{network}/fee', fee.api)
    api.mount('/{chain}/{network}/stats', stats.api)
    api.mount('/{chain}/{network}/tx', tx.api)
    api.mount('/{chain}/{network}/wallet', wallet.api)
    api.mount('/status', status.api)

    api.add_route('/{chain}/{network}/block', block.stream_blocks, include_in_schema=False)
    api.add_route('/{chain}/{network}/tx', tx.stream_transactions, include_in_schema=False)
    api.add_route('/{chain}/{network}/wallet', wallet.create_wallet, methods=['POST'], include_in_schema=False)

    return api


api = build_api()
