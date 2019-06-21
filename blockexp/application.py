from starlette.applications import Starlette

from .api import api


def init_app(*, debug=False) -> Starlette:
    app = Starlette(debug=debug)
    app.mount('/api', api)

    return app
