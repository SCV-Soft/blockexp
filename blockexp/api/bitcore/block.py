from dataclasses import dataclass
from typing import List

from starlette.requests import Request
from starlette.routing import Router

from blockexp.provider import SteamingFindOptions, Direction
from starlette_typed import typed_endpoint
from . import ApiPath
from ...model import Block
from ...provider import Provider

api = Router()


@dataclass
class StreamBlockApiQuery:
    sinceBlock: str
    date: str = None
    limit: int = None
    since: str = None
    direction: Direction = None
    paging: str = None


@api.route('/', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_blocks(request: Request, path: ApiPath, query: StreamBlockApiQuery, provider: Provider) -> List[Block]:
    return await provider.stream_blocks(
        since_block=query.sinceBlock,
        date=query.date,
        find_options=SteamingFindOptions(
            limit=query.limit,
            since=query.since,
            direction=query.direction,
            paging=query.paging,
        )
    )


@api.route('/tip', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_tip(request: Request, path: ApiPath, provider: Provider) -> Block:
    return await provider.get_local_tip()


@dataclass
class BlockIdApiPath(ApiPath):
    block_id: str


@api.route('/{block_id}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_block(request: Request, path: BlockIdApiPath, provider: Provider) -> Block:
    return await provider.get_block(path.block_id)


@dataclass
class BlockBeforeTimeApiPath(ApiPath):
    time: str


@api.route('/before-time/{time}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_block_before_time(request: Request, path: BlockBeforeTimeApiPath, provider: Provider) -> Block:
    raise NotImplementedError
