from dataclasses import dataclass
from typing import List

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from ...blockchain import iter_blockchain

api = Router()


@dataclass
class BlockchainSchema:
    chain: str
    network: str


@api.route('/enabled-chains', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def enabled_chains(request: Request) -> List[BlockchainSchema]:
    blockchains = []
    for blockchain in iter_blockchain(request.app):
        blockchains.append(BlockchainSchema(blockchain.chain, blockchain.network))

    return blockchains
