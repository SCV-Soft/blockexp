from .accessor import EthDaemonAccessor
from .importer import EthDaemonImporter
from .mongo import EthMongoDatabase
from .provider import EthMongoProvider
from ...application import Application
from ...database import MongoDatabase, connect_database_for
from ...types import Blockchain


class EthBlockchain(Blockchain):
    def __init__(self, chain: str, network: str, app: Application, url: str, **config):
        super().__init__(chain, network)
        self.app = app
        self.url = url
        self.config = config

    def get_db(self, database: MongoDatabase) -> EthMongoDatabase:
        return EthMongoDatabase(self.chain, self.network, database)

    async def ready(self):
        async with self.get_accessor() as daemon:
            await daemon.get_local_tip()

        async with connect_database_for(self.app) as database:
            db = self.get_db(database)
            await db.create_indexes()

    def get_accessor(self) -> EthDaemonAccessor:
        return EthDaemonAccessor(self.chain, self.network, self.url)

    def get_importer(self) -> EthDaemonImporter:
        return EthDaemonImporter(self.chain, self.network, self.get_accessor(), self.app)

    def get_provider(self, database: MongoDatabase) -> EthMongoProvider:
        return EthMongoProvider(self.chain, self.network, self.get_db(database), self.get_accessor())
