from abc import ABC, abstractmethod


class Service(ABC):
    @abstractmethod
    async def on_startup(self):
        pass

    @abstractmethod
    async def on_shutdown(self):
        pass
