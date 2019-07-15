from contextlib import asynccontextmanager

from requests import Request

from starlette_typed.endpoint import register_handler
from ..ext.database import MongoDatabase, connect_database


@register_handler
@asynccontextmanager
async def database(request: Request) -> MongoDatabase:
    async with connect_database(request) as database:
        async with database:
            yield database
