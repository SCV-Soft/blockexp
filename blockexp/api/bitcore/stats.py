from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...provider import Provider
from ...provider.base import DailyTransactions

api = Router()


@api.route('/daily-transactions', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_daily_transactions(request: Request, path: ApiPath, provider: Provider) -> DailyTransactions:
    return await provider.get_daily_transactions()
