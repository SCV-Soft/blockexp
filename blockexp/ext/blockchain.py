import asyncio
from typing import Iterator, Optional

from ..application import Application
from ..blockchain import Blockchain
from ..blockchain.btc import BitcoinBlockchain
from ..blockchain.jack import JackBlockchain
from ..service import Service


class ImportBlockchainService(Service):
    def __init__(self, app: Application):
        self.app = app
        self.importers = []
        self.tasks = []

    async def on_startup(self):
        for blockchain in iter_blockchain(self.app):
            importer = blockchain.get_importer()
            if importer is not None:
                task: asyncio.Future = asyncio.ensure_future(importer.run())
                self.importers.append(importer)
                self.tasks.append(task)

    async def on_shutdown(self):
        for task in self.tasks:
            task.cancel()

        for task in self.tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

        del self.importers[:]


def init_app(app: Application) -> dict:
    blockchain_pool = {}
    for chain, networks in app.config["RPC"].items():
        for network, url in networks.items():
            if chain == "BTC":
                blockchain = BitcoinBlockchain(chain, network, app, url)
            elif chain == "JACK":
                blockchain = JackBlockchain(chain, network, app, url)
            elif chain == "ETH":
                raise NotImplementedError
            else:
                continue

            blockchain_pool[chain, network] = blockchain

    app.register_service(ImportBlockchainService(app))
    return blockchain_pool


def get_blockchain_pool(app: Application) -> dict:
    return app.get_extension(__name__)


def get_blockchain(chain: str, network: str, app: Application) -> Optional[Blockchain]:
    chain_pool = get_blockchain_pool(app)
    return chain_pool.get((chain, network))


def iter_blockchain(app: Application) -> Iterator[Blockchain]:
    for chain in get_blockchain_pool(app).values():
        yield chain
