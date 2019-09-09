from abc import ABC, abstractmethod


class Connectable(ABC):
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return None

    @abstractmethod
    async def connect(self):
        raise NotImplementedError

    @abstractmethod
    async def close(self):
        raise NotImplementedError
