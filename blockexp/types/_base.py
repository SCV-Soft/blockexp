from dataclasses import dataclass


@dataclass(init=False)
class Base:
    chain: str
    network: str

    def __init__(self, chain: str, network: str):
        self.chain = chain
        self.network = network
