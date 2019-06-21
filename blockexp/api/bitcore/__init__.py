from starlette.routing import Router
from dataclasses import dataclass


@dataclass
class ApiPath:
    chain: str
    network: str


def build_api() -> Router:
    from . import address, block, fee, stats, tx, wallet

    api = Router()
    api.mount('/{chain}/{network}/address', address.api)
    api.mount('/{chain}/{network}/block', block.api)
    api.mount('/{chain}/{network}/fee', fee.api)
    api.mount('/{chain}/{network}/stats', stats.api)
    api.mount('/{chain}/{network}/tx', tx.api)
    api.mount('/{chain}/{network}/wallet', wallet.api)
    return api


api = build_api()
