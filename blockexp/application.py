from typing import Any

from starlette.applications import Starlette

from .service import Service


class Application(Starlette):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions = {}
        self.config = {}
        self.services = []

        self.on_event("startup")(self.on_startup)
        self.on_event("shutdown")(self.on_shutdown)

    async def on_startup(self):
        for service in self.services:
            await service.on_startup()

    async def on_shutdown(self):
        for service in self.services:
            await service.on_shutdown()

    def register_service(self, service: Service):
        self.services.append(service)

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

    from .ext import database
    app.register_extension(database)

    from .ext import blockchain
    app.register_extension(blockchain)

    from .api import api
    app.mount('/api', api)

    from .ext import swagger
    app.register_extension(swagger)

    return app
