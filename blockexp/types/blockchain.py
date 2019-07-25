from dataclasses import dataclass
from typing import Optional

from .accessor import Accessor
from .importer import Importer
from ..ext.database import MongoDatabase
from .provider import Provider


@dataclass(init=False)
class Blockchain:
    def __init__(self, chain: str, network: str):
        self.chain = chain
        self.network = network

    def get_importer(self) -> Optional[Importer]:
        return None

    def get_accessor(self) -> Accessor:
        raise NotImplementedError

    def get_provider(self, database: MongoDatabase) -> Provider:
        raise NotImplementedError
