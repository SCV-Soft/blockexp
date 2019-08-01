from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from starlette_typed import TypedStarlettePlugin
from starlette_typed.apispec import patch_apispec_orderdict
from ..application import Application

apispec = APISpec(
    title=__package__,
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[
        TypedStarlettePlugin(),
        MarshmallowPlugin(),
    ],
)


async def init_app(app: Application):
    patch_apispec_orderdict()
