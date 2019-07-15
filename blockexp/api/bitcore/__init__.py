from dataclasses import dataclass

from starlette.routing import Router


@dataclass
class ApiPath:
    chain: str
    network: str


def build_api() -> Router:
    from . import address, block, fee, stats, tx, wallet, status

    # noinspection PyShadowingNames
    api = Router()
    api.mount('/{chain}/{network}/address', address.api)
    api.mount('/{chain}/{network}/block', block.api)
    api.mount('/{chain}/{network}/fee', fee.api)
    api.mount('/{chain}/{network}/stats', stats.api)
    api.mount('/{chain}/{network}/tx', tx.api)
    api.mount('/{chain}/{network}/wallet', wallet.api)
    api.mount('/status', status.api)

    api.add_route('/{chain}/{network}/block', block.stream_blocks, include_in_schema=False)
    api.add_route('/{chain}/{network}/tx', tx.stream_transactions, include_in_schema=False)
    api.add_route('/{chain}/{network}/wallet', wallet.create_wallet, methods=['POST'], include_in_schema=False)

    return api


api = build_api()
