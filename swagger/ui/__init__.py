from apispec import APISpec
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Router
from starlette.schemas import OpenAPIResponse
from starlette.staticfiles import StaticFiles

from starlette_typed import TypedStarletteSchemaGenerator


class PlainTextOpenAPIResponse(OpenAPIResponse):
    media_type = PlainTextResponse.media_type


def create_schema_handler(apispec: APISpec):
    schemas = TypedStarletteSchemaGenerator(apispec)

    def schema(request: Request):
        app: Starlette = request.app
        if app.debug:
            schema = schemas.get_schema(routes=app.routes)
            return PlainTextOpenAPIResponse(schema)
        else:
            return schemas.OpenAPIResponse(request)

    return schema


def create_swagger(apispec: APISpec, *, router: Router = None):
    handler = create_schema_handler(apispec)
    router.add_route('/schema', handler, include_in_schema=False)

    router.mount(
        path='/',
        app=StaticFiles(packages=[__package__], html=True),
        name='statics',
    )

    return router
