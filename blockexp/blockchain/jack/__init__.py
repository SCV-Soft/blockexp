from .accessor import JackDaemonAccessor
from ..btc import BtcBlockchain


class JackBlockchain(BtcBlockchain):
    def get_accessor(self) -> JackDaemonAccessor:
        return JackDaemonAccessor(self.chain, self.network, self.url)
