from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...provider import Provider

api = Router()


@api.route('/daily-transactions', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_daily_transactions(request: Request, path: ApiPath, provider: Provider) -> str:
    raise NotImplementedError
