from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...model import EstimateFee
from ...types import Accessor

api = Router()


@dataclass
class GetFeeApiPath(ApiPath):
    target: int = None


@api.route('/{target:int}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_fee(request: Request, path: GetFeeApiPath, accessor: Accessor) -> EstimateFee:
    return await accessor.get_fee(path.target)
