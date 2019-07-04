from http import HTTPStatus

from starlette.exceptions import HTTPException


class HTTPError(HTTPException):
    status_code: HTTPStatus

    def __init__(self, detail: str = None):
        super().__init__(self.status_code, detail)
