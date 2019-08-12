from .accessor import PchDaemonAccessor
from ..btc import BtcBlockchain


class PchBlockchain(BtcBlockchain):
    def get_accessor(self) -> PchDaemonAccessor:
        return PchDaemonAccessor(self.chain, self.network, self.url)
