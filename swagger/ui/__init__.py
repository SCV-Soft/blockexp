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


def create_swagger(apispec: APISpec):
    swagger = Router()
    schemas = TypedStarletteSchemaGenerator(apispec)

    @swagger.route('/schema', include_in_schema=False)
    def schema(request: Request):
        app: Starlette = request.app
        if app.debug:
            schema = schemas.get_schema(routes=app.routes)
            return PlainTextOpenAPIResponse(schema)
        else:
            return schemas.OpenAPIResponse(request)

    swagger.mount(
        path='/',
        app=StaticFiles(packages=[__package__], html=True),
        name='statics',
    )

    return swagger
