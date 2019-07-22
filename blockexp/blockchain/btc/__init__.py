from typing import Optional, Tuple
from urllib.parse import urlparse, ParseResult

from requests.auth import HTTPBasicAuth

from .importer import BitcoinDaemonImporter
from .provider import BitcoinDaemonProvider, BitcoinMongoProvider
from ...application import Application
from ...ext.database import MongoDatabase
from ...types import Blockchain, Provider


def parse_url(url: str) -> Tuple[str, Optional[HTTPBasicAuth]]:
    pr: ParseResult = urlparse(url)
    if pr.username or pr.password:
        assert pr.username and pr.password
        auth = HTTPBasicAuth(pr.username, pr.password)
        url = url.replace(f'{pr.username}:{pr.password}@', '')
    else:
        auth = None

    return url, auth


class BitcoinBlockchain(Blockchain):
    def __init__(self, chain: str, network: str, app: Application, url: str):
        super().__init__(chain, network)
        self.app = app
        self.url, self.auth = parse_url(url)

    def get_importer(self) -> BitcoinDaemonImporter:
        provider = self.get_provider()
        return BitcoinDaemonImporter(self.chain, self.network, provider, self.app)

    def get_provider(self) -> BitcoinDaemonProvider:
        return BitcoinDaemonProvider(self.chain, self.network, self.url, auth=self.auth)

    def get_full_provider(self, database: MongoDatabase) -> Provider:
        return BitcoinMongoProvider(self.chain, self.network, database, self.get_provider())
