from .accessor import BitcoinDaemonAccessor
from .importer import BitcoinDaemonImporter
from .mongo import BtcMongoDatabase
from .provider import BitcoinMongoProvider
from ...application import Application
from ...database import MongoDatabase
from ...types import Blockchain, Provider
from ...utils.url import parse_url


class BitcoinBlockchain(Blockchain):
    def __init__(self, chain: str, network: str, app: Application, url: str):
        super().__init__(chain, network)
        self.app = app
        self.url, self.auth = parse_url(url)

    def get_importer(self) -> BitcoinDaemonImporter:
        return BitcoinDaemonImporter(self.chain, self.network, self.get_accessor(), self.app)

    def get_accessor(self) -> BitcoinDaemonAccessor:
        return BitcoinDaemonAccessor(self.chain, self.network, self.url, auth=self.auth)

    def get_provider(self, database: MongoDatabase) -> Provider:
        db = BtcMongoDatabase(database)
        return BitcoinMongoProvider(self.chain, self.network, db, self.get_accessor())
