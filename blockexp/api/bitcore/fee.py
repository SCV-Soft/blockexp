from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath

api = Router()


@dataclass
class GetFeeApiPath(ApiPath):
    target: int


@api.route('/{target}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_fee(request: Request, path: GetFeeApiPath) -> str:
    raise NotImplementedError
