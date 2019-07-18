from dataclasses import dataclass
from typing import List

from aiocache import cached
from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint, cache_endpoint
from . import ApiPath
from ...model import Block
from ...provider import Provider
from ...provider.base import SteamingFindOptions, Direction

api = Router()


@dataclass
class StreamBlockApiQuery:
    sinceBlock: str = None
    startDate: str = None
    endDate: str = None
    date: str = None
    limit: int = None
    since: int = None
    direction: int = None
    paging: str = None


@api.route('/', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_blocks(request: Request, path: ApiPath, query: StreamBlockApiQuery, provider: Provider) -> List[Block]:
    return await provider.stream_blocks(
        since_block=int(query.sinceBlock) if query.sinceBlock and query.sinceBlock.isdecimal() else query.sinceBlock,
        start_date=query.startDate,
        end_date=query.endDate,
        date=query.date,
        find_options=SteamingFindOptions(
            limit=query.limit,
            since=query.since,
            direction=Direction(query.direction) if query.direction is not None else None,
            paging=query.paging,
        )
    )


@cached(ttl=30)
async def get_cached_local_tip(provider: Provider):
    return await provider.get_local_tip()


@api.route('/tip', methods=['GET'])
@cache_endpoint(ttl=5)
@typed_endpoint(tags=["bitcore"])
async def get_tip(request: Request, path: ApiPath, provider: Provider) -> Block:
    return await get_cached_local_tip(provider)


@dataclass
class BlockIdApiPath(ApiPath):
    block_id: str


@api.route('/{block_id}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_block(request: Request, path: BlockIdApiPath, provider: Provider) -> Block:
    block_id = path.block_id
    if block_id.isdecimal():
        block_id = int(block_id)

    return await provider.get_block(block_id)


@dataclass
class BlockBeforeTimeApiPath(ApiPath):
    time: str


@api.route('/before-time/{time}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_block_before_time(request: Request, path: BlockBeforeTimeApiPath, provider: Provider) -> Block:
    raise NotImplementedError
