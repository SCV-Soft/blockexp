from urllib.parse import urljoin

import requests_async as requests


class AsyncBitcore:
    URL = "https://api.bitcore.io/api/{chain}/{network}/"

    def __init__(self, chain: str, network: str):
        self.url = self.URL.format(chain=chain, network=network)
        self.session = requests.Session()

    def get_url(self, path: str) -> str:
        return urljoin(self.url, path)

    async def get(self, path: str, **kwargs):
        url = self.get_url(path)
        return await self.session.get(url, **kwargs)

    async def post(self, path: str, **kwargs):
        url = self.get_url(path)
        return await self.session.post(url, **kwargs)
