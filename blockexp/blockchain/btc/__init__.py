from .accessor import BtcDaemonAccessor
from .importer import BtcDaemonImporter
from .mongo import BtcMongoDatabase
from .provider import BtcMongoProvider
from ...application import Application
from ...database import MongoDatabase
from ...types import Blockchain, Provider
from ...utils.url import parse_url


class BtcBlockchain(Blockchain):
    def __init__(self, chain: str, network: str, app: Application, url: str):
        super().__init__(chain, network)
        self.app = app
        self.url, self.auth = parse_url(url)

    def get_importer(self) -> BtcDaemonImporter:
        return BtcDaemonImporter(self.chain, self.network, self.get_accessor(), self.app)

    def get_accessor(self) -> BtcDaemonAccessor:
        return BtcDaemonAccessor(self.chain, self.network, self.url, auth=self.auth)

    def get_provider(self, database: MongoDatabase) -> Provider:
        db = BtcMongoDatabase(self.chain, self.network, database)
        return BtcMongoProvider(self.chain, self.network, db, self.get_accessor())
