from .accessor import AbleDaemonAccessor
from ..btc import BtcBlockchain


class AbleBlockchain(BtcBlockchain):
    def get_accessor(self) -> AbleDaemonAccessor:
        return AbleDaemonAccessor(self.chain, self.network, self.url)
