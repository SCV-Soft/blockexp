from .database import database
from .provider import provider
from ..application import Application

FIXTURES = {database, provider}


async def init_app(app: Application):
    # check register_handler function
    for _ in FIXTURES:
        pass
