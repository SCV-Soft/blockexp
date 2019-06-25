from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...model import Block
from ...provider import Provider

api = Router()


@dataclass
class StreamBlockApiQuery:
    sinceBlock: str
    date: str
    limit: int
    since: str
    direction: str
    paging: str


@api.route('/', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_blocks(request: Request, path: ApiPath, query: StreamBlockApiQuery, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/tip', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_tip(request: Request, path: ApiPath, provider: Provider) -> str:
    raise NotImplementedError


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
async def get_local_tip(request: Request, path: BlockBeforeTimeApiPath, provider: Provider) -> str:
    raise NotImplementedError
