from abc import ABC, abstractmethod

from ._base import Base


class Importer(Base, ABC):
    @abstractmethod
    async def run(self):
        raise NotImplementedError
