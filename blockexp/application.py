from typing import Any

from starlette.applications import Starlette

from swagger.ui import create_swagger
from .api import api, apispec


class Application(Starlette):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions = {}
        self.config = {}

    def get_extension(self, name: str):
        return self.extensions[name]

    def register_extension(self, extension: Any):
        self.extensions[extension.__name__] = extension.init_app(self)


def init_app(*, debug=False) -> Starlette:
    app = Application(debug=debug)

    from . import config
    app.config.update({
        key: value
        for key, value in vars(config).items()
        if not key.startswith('_')
    })

    app.mount('/api', api)
    app.mount('/', create_swagger(apispec))

    return app
