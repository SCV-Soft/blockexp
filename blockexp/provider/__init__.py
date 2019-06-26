from contextlib import asynccontextmanager

from starlette.requests import Request

from starlette_typed.endpoint import register_handler
from .base import Provider
from .bitcore import BitcoreProvider


@register_handler
@asynccontextmanager
async def provider(request: Request) -> Provider:
    path_params = request.path_params
    chain = path_params['chain']
    network = path_params['network']

    # noinspection PyShadowingNames
    provider = get_provider(chain, network)

    async with provider:
        yield provider


def get_provider(chain: str, network: str) -> Provider:
    if chain == "BTC" or chain == "BCH":
        return BitcoreProvider(chain, network)
    else:
        raise NotImplementedError((chain, network))
