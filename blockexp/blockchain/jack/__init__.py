from .accessor import JackDaemonAccessor
from ..btc import BitcoinBlockchain


class JackBlockchain(BitcoinBlockchain):
    def get_accessor(self) -> JackDaemonAccessor:
        return JackDaemonAccessor(self.chain, self.network, self.url, auth=self.auth)
