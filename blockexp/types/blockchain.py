from abc import ABC, abstractmethod
from typing import Optional, Any

from ._base import Base
from .accessor import Accessor
from .importer import Importer
from .provider import Provider


class Blockchain(Base, ABC):
    async def ready(self):
        pass

    def get_importer(self) -> Optional[Importer]:
        return None

    @abstractmethod
    def get_accessor(self) -> Accessor:
        raise NotImplementedError

    @abstractmethod
    def get_provider(self, database: Any) -> Provider:
        raise NotImplementedError
