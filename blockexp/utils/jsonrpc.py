from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any, Optional, Union, List, Callable

import requests_async as requests
import websockets
from h11 import RemoteProtocolError
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests_async import Response

from .url import get_scheme, parse_url


class JSONRPCException(Exception):
    pass


class JSONRPCConnectionError(JSONRPCException):
    pass


class JSONRPCUnauthorized(JSONRPCException):
    pass


class JSONRPCInvalidResponse(JSONRPCException):
    message: str
    response: Response

    def __init__(self, message: str, response: Response):
        super().__init__(message)
        self.message = message
        self.response = response

    def __str__(self):
        return f'{self.message}\n{self.response.text}'


class JSONRPCError(JSONRPCException):
    def __init__(self, code: int = None, message: str = None, data: Any = None):
        super().__init__((code, message, data) if data is not None else (code, message))
        self.code = code
        self.message = message
        self.data = data

    def __str__(self):
        return f'{self.message} (code={self.code!r})'

    @classmethod
    def parse(cls, data: Optional[Union[JSONRPCError, dict]]) -> Optional[JSONRPCError]:
        if data is None:
            return None
        elif isinstance(data, JSONRPCError):
            return data

        return JSONRPCError(**data)


def jsonrpc20_call(id: int, method: str, args: Union[list, tuple], kwargs: dict) -> dict:
    if args and kwargs:
        raise ValueError

    return {"jsonrpc": "2.0", "method": method, "params": kwargs or args, "id": id}


@dataclass(init=False)
class JsonRpcRequest:
    method: str
    params: Union[list, tuple, dict]

    def __init__(self, method: str, params: Union[list, tuple, dict]):
        self.method = method
        self.params = params

    def build(self, id: int = 0):
        return {
            'jsonrpc': '2.0',
            'method': self.method,
            'params': self.params,
            'id': id,
        }


@dataclass(init=False)
class JsonRpcResponse:
    id: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None

    def __init__(self,
                 id: Optional[int] = None,
                 result: Optional[Any] = None,
                 error: Union[Optional[dict, JSONRPCError]] = None):
        self.id = id
        self.result = result
        self.error = JSONRPCError.parse(error)


def parse_data(data: dict) -> Union[JsonRpcRequest, JsonRpcResponse]:
    if not isinstance(data, dict):
        raise TypeError

    is_request = 'method' in data or 'params' in data
    is_response = 'id' in data or 'data' in data or 'error' in data

    if is_request and is_response:
        raise ValueError

    if is_request:
        return JsonRpcRequest(
            method=data.get('method'),
            params=data.get('params'),
        )
    elif is_response:
        return JsonRpcResponse(
            id=data.get('id'),
            result=data.get('result'),
            error=data.get('error'),
        )
    else:
        raise ValueError


class AsyncTunnel:
    async def connect(self):
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError

    async def reset(self):
        if self.closed:
            await self.close()

        await self.connect()

    @property
    def closed(self) -> bool:
        raise NotImplementedError

    @property
    def has_event(self):
        return False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return self

    async def call(self, method: str, *args, **kwargs) -> Any:
        raise NotImplementedError

    async def batch(self, reqs: List[JsonRpcRequest]) -> List[Any]:
        raise NotImplementedError

    async def event(self, method: str, callback: Callable):
        raise NotImplementedError


class AsyncRequestsTunnel(AsyncTunnel):
    session: Optional[requests.Session]

    def __init__(self, url: str):
        self.url, self.auth = parse_url(url)
        self.session = None

    async def connect(self):
        self.session = requests.Session()

    async def close(self):
        await self.session.close()
        self.session = None

    @property
    def closed(self) -> bool:
        return self.session is None

    async def call(self, method, *args, **kwargs) -> Any:
        assert not self.closed

        data = jsonrpc20_call(0, method, args, kwargs)
        response: Optional[Response] = None

        for repeat in range(5):
            try:
                response = await self.session.post(
                    self.url,
                    json=data,
                    auth=self.auth,
                )
            except (RemoteProtocolError, RequestsConnectionError) as e:
                if repeat >= 4:
                    raise JSONRPCConnectionError from e

                await asyncio.sleep(0.5)
                continue
            else:
                break

        # 401 error code
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise JSONRPCUnauthorized('Unauthorized error')

        try:
            data = response.json()
        except JSONDecodeError as e:
            raise JSONRPCInvalidResponse('invalid json', response=response) from e

        resp = parse_data(data)
        if not isinstance(resp, JsonRpcResponse):
            raise JSONRPCInvalidResponse('invalid jsonrpc response', response=response)

        if resp.id != 0:
            raise JSONRPCException("invalid result", resp.id)

        if resp.error:
            raise resp.error

        return resp.result

    async def batch(self, reqs: List[JsonRpcRequest]) -> List[Any]:
        raise NotImplementedError

    async def event(self, method: str, callback: Callable):
        raise NotImplementedError


class AsyncWebsocketTunnel(AsyncTunnel):
    socket: Optional[websockets.WebSocketClientProtocol]

    def __init__(self, url, auth: HTTPBasicAuth = None):
        self.url = url
        self.auth = auth
        self._socket = None

        # persist state
        self._events = {}
        self._reconnected_callback = None

        # connection state
        self._id = 0
        self._results = {}
        self._task = None

    async def connect(self):
        assert self.closed
        self.socket = await websockets.connect(self.url)
        self._task = asyncio.ensure_future(self.loop())
        if self._reconnected_callback is not None:
            await self._reconnected_callback()

    async def close(self):
        if not self.closed:
            self.socket.close()
            self.socket = None
            self._task.cancel()

    async def reset(self):
        await super().reset()
        self._id = 0
        self._results.clear()

    @property
    def closed(self):
        return self.socket is None or self.socket.closed

    def on_result(self, result_id: int) -> asyncio.Future:
        future = asyncio.get_event_loop().create_future()
        self._results[result_id] = future
        return future

    def on_reconnected(self, callback):
        self._reconnected_callback = callback

    async def loop(self):
        keepalive = asyncio.ensure_future(self.socket.keepalive_ping())

        try:
            while not keepalive.done():
                data = await self.socket.recv()
                await self.process_data(data)

            raise keepalive.exception()
        except Exception as e:
            for future in self._results.values():
                future.set_exception(e)

            if not keepalive.done():
                keepalive.cancel()

            raise

    async def process_data(self, data):
        resp = parse_data(data)
        if isinstance(resp, JsonRpcRequest):
            func = self._events.get(resp.method)
            if isinstance(resp.params, (list, tuple)):
                func(*resp.params)
            elif isinstance(resp.params, dict):
                func(**resp.params)
            else:
                pass  # TODO: error
        elif isinstance(resp, JsonRpcResponse):
            future: Optional[asyncio.Future] = self._results.get(resp.id)
            if resp.error is not None:
                future.set_exception(resp.error)
            else:
                future.set_result(resp.result)
        else:
            assert False

    def _get_next_id(self):
        self._id += 1
        return self._id

    async def call(self, method: str, *args, **kwargs) -> Any:
        result_id = self._get_next_id()
        data = jsonrpc20_call(result_id, method, args, kwargs)

        future = self.on_result(result_id)
        await self.socket.send(data)

        return await future

    async def batch(self, reqs: List[JsonRpcRequest]) -> List[Any]:
        raise NotImplementedError

    async def event(self, method: str, callback: Callable):
        self._events[method] = callback


# noinspection PyPep8Naming
class AsyncJsonRPC(AsyncTunnel):
    tunnel: AsyncTunnel

    SCHEME_TUNNELS = {
        "http": AsyncRequestsTunnel,
        "https": AsyncRequestsTunnel,
        "ws": AsyncWebsocketTunnel,
        "wss": AsyncWebsocketTunnel,
    }

    def __init__(self, url: str):
        self.url = url
        self.tunnel = self.build_tunnel(url)

    @classmethod
    def build_tunnel(cls, url: str):
        scheme = get_scheme(url)
        tunnel_cls = cls.SCHEME_TUNNELS[scheme]
        return tunnel_cls(url)

    async def connect(self):
        await self.tunnel.connect()

    async def close(self):
        await self.tunnel.close()

    @property
    def closed(self) -> bool:
        return self.tunnel.closed

    async def call(self, method: str, *args, **kwargs) -> Any:
        return await self.tunnel.call(method, *args, **kwargs)

    async def batch(self, reqs: List[JsonRpcRequest]) -> List[Any]:
        return await self.tunnel.batch(reqs)

    async def event(self, method: str, callback: Callable):
        return self.tunnel.event(method, callback)
