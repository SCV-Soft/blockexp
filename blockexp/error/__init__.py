from http import HTTPStatus
from typing import Union

from starlette.exceptions import HTTPException


class HTTPError(HTTPException):
    status_code: Union[HTTPStatus, int]

    def __init__(self, detail: str = None):
        status_code = self.status_code
        if isinstance(self.status_code, HTTPStatus):
            status_code = status_code.value

        super().__init__(status_code, f'{type(self).__name__}: {detail}')


class NotFound(HTTPError):
    status_code = HTTPStatus.NOT_FOUND


class ObjectNotFound(NotFound, KeyError):
    pass


class BlockNotFound(ObjectNotFound):
    pass


class TransactionNotFound(ObjectNotFound):
    pass


class AddressNotFound(ObjectNotFound):
    pass
