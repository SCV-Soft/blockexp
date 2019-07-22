from dataclasses import dataclass
from typing import Optional

from .importer import Importer
from .provider import Provider, RawProvider
from ..ext.database import MongoDatabase


@dataclass(init=False)
class Blockchain:
    def __init__(self, chain: str, network: str):
        self.chain = chain
        self.network = network

    def get_importer(self) -> Optional[Importer]:
        return None

    def get_provider(self) -> RawProvider:
        raise NotImplementedError

    def get_full_provider(self, database: MongoDatabase) -> Provider:
        raise NotImplementedError
