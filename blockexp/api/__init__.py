from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from starlette.routing import Router

from starlette_typed import TypedStarlettePlugin
from starlette_typed.apispec import patch_apispec_orderdict
from . import bitcore

patch_apispec_orderdict()

apispec = APISpec(
    title=__package__,
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[
        TypedStarlettePlugin(),
        MarshmallowPlugin(),
    ],
)

api = Router()
# api.mount('/eth', eth.api)
api.mount('/', bitcore.api)
