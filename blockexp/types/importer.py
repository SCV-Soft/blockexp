from ._base import Base


class Importer(Base):
    async def run(self):
        raise NotImplementedError
