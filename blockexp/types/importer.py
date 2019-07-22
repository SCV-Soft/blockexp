from dataclasses import dataclass


@dataclass(init=False)
class Importer:
    chain: str
    network: str

    def __init__(self, chain: str, network: str):
        self.chain = chain
        self.network = network

    async def run(self):
        raise NotImplementedError
