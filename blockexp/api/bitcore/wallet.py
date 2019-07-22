import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import List

from bitcoinlib.encoding import double_sha256
from bitcoinlib.keys import Key
from bitcoinlib.transactions import verify
from starlette.requests import Request
from starlette.routing import Router

from starlette_typed import typed_endpoint
from starlette_typed.endpoint import register_handler
from . import ApiPath
from ...model import Wallet, Coin, Balance, Transaction, WalletCheckResult
from ...model.options import SteamingFindOptions
from ...types import Provider

api = Router()


@dataclass
class WalletApiPath(ApiPath):
    pub_key: str


@dataclass
class CreateWalletApiBody:
    chain: str
    network: str
    name: str
    pubKey: str
    path: str = None
    singleAddress: bool = None


@api.route('/', methods=['POST'])
@typed_endpoint(tags=["bitcore"])
async def create_wallet(request: Request, path: ApiPath, body: CreateWalletApiBody, provider: Provider) -> Wallet:
    return await provider.create_wallet(
        name=body.name,
        pub_key=body.pubKey,
        path=body.path,
        single_address=body.singleAddress,
    )


@register_handler
@asynccontextmanager
async def wallet(request: Request) -> Wallet:
    provider: Provider = request.scope['provider']
    pub_key: str = request.path_params['pub_key']

    # noinspection PyShadowingNames
    wallet = await provider.get_wallet(pub_key)

    message = '|'.join([
        request.method,
        request.url.path if not request.url.query else f'{request.url.path}?{request.url.query}',
        (await request.body()).decode('utf-8', errors='replace') or '{}',
    ]).encode('utf-8')

    message_hash = double_sha256(message)
    key = Key(pub_key)

    x_signature = request.headers.get('x-signature', '')
    signature = base64.b16decode(x_signature, casefold=True)

    if not signature:
        raise Exception('Signature must exist')

    if not verify(message_hash, signature, key):
        raise Exception('Verify signature failure')

    yield wallet


@dataclass
class WalletAddressItem:
    address: str


@dataclass
class LimitApiQuery:
    limit: int = None
    ...  # hidden argument for provider.streamWalletUtxos or provider.streamWalletTransactions


@api.route('/{pub_key}/addresses/missing', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_missing_wallet_addresses(request: Request, path: WalletApiPath, provider: Provider,
                                          wallet: Wallet) -> List[WalletAddressItem]:
    return [WalletAddressItem(address) for address in await provider.stream_missing_wallet_addresses(wallet)]


@api.route('/{pub_key}/addresses', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_wallet_addresses(request: Request, path: WalletApiPath, query: LimitApiQuery,
                                  provider: Provider, wallet: Wallet) -> List[WalletAddressItem]:
    return [WalletAddressItem(item.address)
            for item in await provider.stream_wallet_addresses(wallet, query.limit)]


@api.route('/{pub_key}/check', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def wallet_check(request: Request, path: WalletApiPath, provider: Provider, wallet: Wallet) -> WalletCheckResult:
    return await provider.wallet_check(wallet)


@api.route('/{pub_key}', methods=['POST'])
@typed_endpoint(tags=["bitcore"])
async def update_wallet(request: Request, path: WalletApiPath, provider: Provider, wallet: Wallet,
                        body: List[WalletAddressItem]) -> Wallet:
    await provider.update_wallet(wallet, [item.address for item in body])
    return wallet


@dataclass
class WalletTransactionQuery:
    startBlock: int = None
    endBlock: int = None
    startDate: str = None
    endDate: str = None
    includeMempool: bool = None


@api.route('/{pub_key}/transactions', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_wallet_transactions(request: Request, path: WalletApiPath, query: WalletTransactionQuery,
                                     provider: Provider, wallet: Wallet) -> List[Transaction]:
    return await provider.stream_wallet_transactions(
        wallet,
        start_block=query.startBlock,
        end_block=query.endBlock,
        start_date=query.startDate,
        end_date=query.endDate,
        # includeMempool is ignored
        find_options=SteamingFindOptions(),
    )


@api.route('/{pub_key}/balance', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_wallet_balance(request: Request, path: WalletApiPath, provider: Provider, wallet: Wallet) -> Balance:
    return await provider.get_wallet_balance(wallet)


@dataclass
class WalletTimeApiRequest(WalletApiPath):
    time: str


@api.route('/{pub_key}/balance/{time}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_wallet_balance_at_time(request: Request, path: WalletTimeApiRequest, provider: Provider,
                                     wallet: Wallet) -> Balance:
    return await provider.get_wallet_balance_at_time(wallet, path.time)


@dataclass
class WalletUtxosApiQuery(LimitApiQuery):
    includeSpent: bool = False


@api.route('/{pub_key}/utxos', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def stream_wallet_utxos(request: Request, path: WalletApiPath, query: WalletUtxosApiQuery,
                              provider: Provider, wallet: Wallet) -> List[Coin]:
    return await provider.stream_wallet_utxos(wallet, query.limit, query.includeSpent)


@api.route('/{pub_key}', methods=['GET'])
@typed_endpoint(tags=["bitcore"])
async def get_wallet(request: Request, path: WalletApiPath, provider: Provider, wallet: Wallet) -> Wallet:
    # already loaded by wallet fixture
    return wallet
