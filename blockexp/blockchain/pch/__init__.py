from .provider import PchDaemonProvider
from ..btc import BitcoinBlockchain


class PchBlockchain(BitcoinBlockchain):
    def get_provider(self) -> PchDaemonProvider:
        return PchDaemonProvider(self.chain, self.network, self.url, auth=self.auth)
