import asyncio
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any, Tuple, Optional

import requests_async as requests
from h11 import RemoteProtocolError
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests_async import Response


class JSONRPCException(Exception):
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


def jsonrpc20_call(method: str, *params, id: int = 0) -> dict:
    return {"jsonrpc": "2.0", "method": method, "params": params, "id": id}


def jsonrpc20_result(result: dict) -> Tuple[Optional[int], Optional[Any], Optional[JSONRPCError]]:
    if not isinstance(result, dict):
        raise TypeError

    result_id = result.get('id')

    error = result.get('error')
    if error is not None:
        return result_id, None, JSONRPCError(**error)

    result = result.get('result')
    return result_id, result, None


class AsyncRequestsTunnel:
    def __init__(self, url: str):
        self.url, self.auth = parse_url(url)
        self.session = requests.Session()

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def call(self, method, *params) -> Any:
        response: Optional[Response] = None

        for repeat in range(5):
            try:
                response = await self.session.post(
                    self.url,
                    json=jsonrpc20_call(method, *params),
                    auth=self.auth,
                )
            except (RemoteProtocolError, RequestsConnectionError):
                if repeat >= 4:
                    raise

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

        result_id, result, error = jsonrpc20_result(data)
        if result_id != 0:
            raise JSONRPCException("invalid result", result_id)

        if error:
            raise error

        return result


# noinspection PyPep8Naming
class AsyncJsonRPC:
    tunnel: Union[AsyncRequestsTunnel, AsyncWebsocketTunnel]

    SCHEME_TUNNELS = {
        "http": AsyncRequestsTunnel,
        "https": AsyncRequestsTunnel,
    }

    def __init__(self, url: str):
        self.url = url
        self.tunnel = self.build_tunnel(url)

    @classmethod
    def build_tunnel(cls, url: str):
        scheme = get_scheme(url)
        tunnel_cls = cls.SCHEME_TUNNELS[scheme]
        return tunnel_cls(url)

    async def __aenter__(self):
        await self.tunnel.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.tunnel.__aexit__(exc_type, exc_val, exc_tb)

    async def call(self, method, *params) -> Any:
        return await self.tunnel.call(method, *params)

    # TODO: batch?
