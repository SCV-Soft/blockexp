import asyncio
from typing import Iterator, Optional, List, Tuple

from .btc import BtcBlockchain
from .eth import EthBlockchain
from .jack import JackBlockchain
from .pch import PchBlockchain
from ..application import Application
from ..types import Blockchain, Service

CHAINS = {
    "BTC": BtcBlockchain,
    "ETH": EthBlockchain,
    "JACK": JackBlockchain,
    "PCH": PchBlockchain,
}


class ImportBlockchainService(Service):
    def __init__(self, app: Application):
        self.app = app
        self.futures: List[Tuple[Blockchain, asyncio.Future]] = []

    async def on_startup(self):
        for blockchain in iter_blockchain(self.app):
            self.run_service(blockchain)

    def run_service(self, blockchain: Blockchain):
        importer = blockchain.get_importer()
        if importer is not None:
            future: asyncio.Future = asyncio.ensure_future(importer.run())
            self.futures.append((blockchain, future))

    async def run(self):
        while True:
            for _, future in self.futures:
                if future.cancelled():
                    pass
                elif future.done():
                    exc = future.exception()
                    if exc is None:
                        pass

            await asyncio.sleep(30)

    async def on_shutdown(self):
        for _, task in self.futures:
            if not task.done():
                task.cancel()

        while self.futures:
            _, task = self.futures.pop()

            try:
                await task
            except asyncio.CancelledError:
                pass


async def init_app(app: Application) -> dict:
    blockchain_pool = {}
    for cfg in app.config.get("blockchain", []):
        if not cfg.get('enabled', True):
            continue

        data = cfg.copy()
        data.pop('enabled', None)

        chain = data.pop('chain')
        network = data.pop('network')
        blockchain_type = data.pop("type", chain)

        if not isinstance(blockchain_type, str) or not blockchain_type:
            raise ValueError("Invalid blockchain config: {!r}".format(cfg))

        blockchain_type = blockchain_type.upper()

        blockchain_cls = CHAINS.get(blockchain_type)
        if blockchain_cls is None:
            raise NotImplementedError(blockchain_type)

        blockchain: Blockchain = blockchain_cls(
            chain=chain,
            network=network,
            app=app,
            **data,
        )

        await blockchain.ready()

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
