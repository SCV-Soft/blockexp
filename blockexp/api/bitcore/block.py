from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath

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
async def stream_blocks(request: Request, path: ApiPath, query: StreamBlockApiQuery) -> str:
    raise NotImplementedError


@api.route('/tip', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_tip(request: Request, path: ApiPath) -> str:
    raise NotImplementedError


@dataclass
class BlockIdApiPath(ApiPath):
    block_id: str


@api.route('/{block_id}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_block(request: Request, path: BlockIdApiPath) -> str:
    raise NotImplementedError


@dataclass
class BlockBeforeTimeApiPath(ApiPath):
    time: str


@api.route('/before-time/{time}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_local_tip(request: Request, path: BlockBeforeTimeApiPath) -> str:
    raise NotImplementedError
