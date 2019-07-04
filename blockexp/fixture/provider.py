from contextlib import asynccontextmanager

from starlette.requests import Request

from starlette_typed.endpoint import register_handler
from ..ext.blockchain import get_blockchain
from ..ext.database import connect_database
from ..provider.base import Provider


@register_handler
@asynccontextmanager
async def provider(request: Request) -> Provider:
    path_params = request.path_params
    chain = path_params['chain']
    network = path_params['network']

    async with connect_database(request) as database:
        blockchain = get_blockchain(chain, network, request.app)
        if blockchain is None:
            raise NotImplementedError((chain, network))

        # noinspection PyShadowingNames
        async with blockchain.with_full_provider(database) as provider:
            yield provider
