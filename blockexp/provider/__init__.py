from contextlib import asynccontextmanager

from requests.auth import HTTPBasicAuth
from starlette.requests import Request

from starlette_typed.endpoint import register_handler
from .base import Provider, Direction, SteamingFindOptions
from .bitcoind import BitcoinDaemonProvider
from .bitcore import BitcoreProvider


@register_handler
@asynccontextmanager
async def provider(request: Request) -> Provider:
    path_params = request.path_params
    chain = path_params['chain']
    network = path_params['network']

    # noinspection PyShadowingNames
    provider = get_provider(request, chain, network)

    async with provider:
        yield provider


def get_provider(request: Request, chain: str, network: str) -> Provider:
    if chain == "BTC" and network == "localnet":
        return BitcoinDaemonProvider(
            chain,
            network,
            "http://127.0.0.1:18332",
            auth=HTTPBasicAuth("user", "password"),
        )
    elif chain == "BTC" or chain == "BCH":
        return BitcoreProvider(chain, network)
    else:
        raise NotImplementedError((chain, network))
