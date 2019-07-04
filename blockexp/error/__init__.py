from http import HTTPStatus

from starlette.exceptions import HTTPException


class HTTPError(HTTPException):
    status_code: HTTPStatus

    def __init__(self, detail: str = None):
        super().__init__(self.status_code, detail)


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
