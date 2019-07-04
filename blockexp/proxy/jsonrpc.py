from typing import Any, Tuple, Optional

import requests_async as requests
from h11 import RemoteProtocolError
from requests.auth import HTTPBasicAuth
from requests_async import Response
from requests.exceptions import ConnectionError as RequestsConnectionError


class JSONRPCException(Exception):
    pass


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


# noinspection PyPep8Naming
class AsyncJsonRPC:
    def __init__(self, url: str, *, auth: HTTPBasicAuth = None):
        self.url = url
        self.auth = auth
        self.session = requests.Session()

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def call(self, method, *params) -> Any:
        response: Optional[Response] = None

        for repeat in range(3):
            try:
                response = await self.session.post(
                    self.url,
                    json=jsonrpc20_call(method, *params),
                    auth=self.auth,
                )
            except (RemoteProtocolError, RequestsConnectionError):
                if repeat >= 2:
                    raise

                continue
            else:
                break

        result_id, result, error = jsonrpc20_result(response.json())
        if result_id != 0:
            raise JSONRPCException("invalid result", result_id)

        if error:
            raise error

        return result

    # TODO: batch?
