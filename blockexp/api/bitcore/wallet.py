from dataclasses import dataclass

from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from . import ApiPath
from ...provider import Provider

api = Router()


@dataclass
class WalletApiPath(ApiPath):
    pub_key: str


@dataclass
class CreateWalletApiBody:
    name: str
    pubKey: str
    path: str
    singleAddress: str


@api.route('/', methods=['POST'])
@typed_endpoint(tags=["bitcore"])
async def create_wallet(request: Request, path: ApiPath, body: CreateWalletApiBody, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}/addresses/missing', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_missing_wallet_addresses(request: Request, path: WalletApiPath, provider: Provider) -> str:
    raise NotImplementedError


@dataclass
class LimitApiQuery:
    limit: int
    ...  # hidden argument for provider.streamWalletUtxos or provider.streamWalletTransactions


@api.route('/{pub_key}/addresses', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_wallet_addresses(request: Request, path: WalletApiPath, query: LimitApiQuery,
                                  provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}/check', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def wallet_check(request: Request, path: WalletApiPath, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}', methods=['POST'])
@typed_endpoint(tags=["bitcore"])
async def update_wallet(request: Request, path: WalletApiPath, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}/transactions', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_wallet_transactions(request: Request, path: WalletApiPath, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}/balance', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_wallet_balance(request: Request, path: WalletApiPath, provider: Provider) -> str:
    raise NotImplementedError


@dataclass
class WalletTimeApiRequest(WalletApiPath):
    time: str


@api.route('/{pub_key}/balance/{time}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_wallet_balance_at_time(request: Request, path: WalletTimeApiRequest, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}/utxos', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_wallet_utxos(request: Request, path: WalletApiPath, query: LimitApiQuery, provider: Provider) -> str:
    raise NotImplementedError


@api.route('/{pub_key}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def pubkey(request: Request, path: WalletApiPath, provider: Provider) -> str:
    raise NotImplementedError
