from typing import Any

import socketio
import uvicorn
from starlette.applications import Starlette

from .types import Service


class Application(Starlette):
    def __init__(self, *, config: dict, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.extensions = {}
        self.services = []
        self.sio = socketio.AsyncServer(async_mode='asgi')

        self.on_event("startup")(self.on_startup)
        self.on_event("shutdown")(self.on_shutdown)

    def ready(self) -> socketio.ASGIApp:
        return socketio.ASGIApp(self.sio, self)

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

    async def register_extension(self, extension: Any):
        self.extensions[extension.__name__] = await extension.init_app(self)

    def serve(self):
        server_config = self.config.get('server', {})

        uvicorn.run(
            self.ready(),
            host=server_config.get('host', '127.0.0.1'),
            port=server_config.get('port', 8000),
        )


async def init_app(config: dict, *, debug=False) -> Application:
    app = Application(config=config, debug=debug)

    from . import database
    await app.register_extension(database)

    from . import blockchain
    await app.register_extension(blockchain)

    from .ext import apispec
    await app.register_extension(apispec)

    from .api import bitcore
    app.mount('/api/', bitcore.api)

    from .ext import swagger
    await app.register_extension(swagger)

    return app
