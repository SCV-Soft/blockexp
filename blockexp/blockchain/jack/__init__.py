from .provider import JackDaemonProvider
from ..btc import BitcoinBlockchain


class JackBlockchain(BitcoinBlockchain):
    def get_provider(self) -> JackDaemonProvider:
        return JackDaemonProvider(self.chain, self.network, self.url, auth=self.auth)
