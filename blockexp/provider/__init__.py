from contextlib import asynccontextmanager

from requests.auth import HTTPBasicAuth
from starlette.requests import Request

from starlette_typed.endpoint import register_handler
from .base import Provider, Direction, SteamingFindOptions
from .bitcoind import BitcoinDaemonProvider, BitcoinMongoProvider
from .bitcore import BitcoreProvider
from ..ext.database import MongoDatabase, connect_database


@register_handler
@asynccontextmanager
async def provider(request: Request) -> Provider:
    path_params = request.path_params
    chain = path_params['chain']
    network = path_params['network']

    async with connect_database(request) as database:
        # noinspection PyShadowingNames
        provider = get_provider(request, chain, network, database)
        async with provider:
            yield provider


def get_provider(request: Request, chain: str, network: str, database: MongoDatabase) -> Provider:
    def get_bitcoind_provider():
        return BitcoinDaemonProvider(
            chain,
            network,
            "http://127.0.0.1:18332",
            auth=HTTPBasicAuth("user", "password"),
        )

    if chain == "BTC" and network == "testnet":
        provider = get_bitcoind_provider()
        return BitcoinMongoProvider(chain, "localnet", database, provider)
    elif chain == "BTC" and network == "localnet":
        return get_bitcoind_provider()
    elif chain == "BTC" or chain == "BCH":
        return BitcoreProvider(chain, network)
    else:
        raise NotImplementedError((chain, network))
