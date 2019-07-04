from .btc import BitcoinBlockchain

from ..provider.bitcoind import JackDaemonProvider


class JackBlockchain(BitcoinBlockchain):
    def get_provider(self) -> JackDaemonProvider:
        return JackDaemonProvider(self.chain, self.network, self.url, auth=self.auth)
