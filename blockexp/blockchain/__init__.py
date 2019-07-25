import asyncio
from typing import Iterator, Optional, Dict

from .btc import BtcBlockchain
from .jack import JackBlockchain
from .pch import PchBlockchain
from ..application import Application
from ..types import Blockchain, Service


class ImportBlockchainService(Service):
    def __init__(self, app: Application):
        self.app = app
        self.tasks: Dict[Blockchain, asyncio.Task] = {}
        self.watcher = None

    async def on_startup(self):
        for blockchain in iter_blockchain(self.app):
            self.run_service(blockchain)

        # self.watcher = asyncio.ensure_future(self.run())

    def run_service(self, blockchain: Blockchain):
        importer = blockchain.get_importer()
        if importer is not None:
            task: asyncio.Future = asyncio.ensure_future(importer.run())
            self.tasks[blockchain] = task

    async def run(self):
        while True:
            for service, task in self.tasks.items():
                if task.cancelled():
                    pass
                elif task.done():
                    exc = task.exception()
                    if exc is None:
                        pass

            await asyncio.sleep(30)

    async def on_shutdown(self):
        for task in self.tasks.values():
            task.cancel()

        while self.tasks:
            _, task = self.tasks.popitem()

            try:
                await task
            except asyncio.CancelledError:
                pass


async def init_app(app: Application) -> dict:
    blockchain_pool = {}
    for chain, networks in app.config["RPC"].items():
        for network, url in networks.items():
            if chain == "BTC":
                blockchain = BtcBlockchain(chain, network, app, url)
            elif chain == "JACK":
                blockchain = JackBlockchain(chain, network, app, url)
            elif chain == "PCH":
                blockchain = PchBlockchain(chain, network, app, url)
            else:
                raise NotImplementedError(chain)

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
