from starlette.applications import Starlette

from swagger.ui import create_swagger
from .api import api, apispec


def init_app(*, debug=False) -> Starlette:
    app = Starlette(debug=debug)
    app.mount('/api', api)
    app.mount('/', create_swagger(apispec))

    return app
