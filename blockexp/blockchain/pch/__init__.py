from .accessor import PchDaemonAccessor
from ..btc import BitcoinBlockchain


class PchBlockchain(BitcoinBlockchain):
    def get_accessor(self) -> PchDaemonAccessor:
        return PchDaemonAccessor(self.chain, self.network, self.url, auth=self.auth)
