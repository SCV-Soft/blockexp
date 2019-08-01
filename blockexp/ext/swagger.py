import yaml
from starlette.requests import Request
from starlette.routing import Router
from starlette.schemas import OpenAPIResponse

from starlette_typed import TypedStarletteSchemaGenerator
from swagger.ui import create_swagger
from .apispec import apispec
from ..application import Application

REPLACE_PATH = False


def fill_default_value(content: dict, chain: str, network: str):
    if REPLACE_PATH:
        content['paths'] = {path.replace('{chain}', chain).replace('{network}', network): endpoint
                            for path, endpoint in
                            content['paths'].items()}

    for endpoint in content['paths'].values():
        for method, data in endpoint.items():
            parameters = data.get('parameters')
            if parameters is not None:
                if REPLACE_PATH:
                    data['parameters'] = [
                        parameter
                        for parameter in parameters
                        if parameter['name'] not in ('chain', 'network')
                    ]
                else:
                    for parameter in parameters:
                        for name, value in ('chain', chain), ('network', network):
                            if parameter['name'] == name:
                                parameter['schema']['default'] = value


async def custom_schema(request: Request):
    schemas = TypedStarletteSchemaGenerator(apispec)
    response = schemas.OpenAPIResponse(request)
    content = yaml.load(response.body, Loader=yaml.SafeLoader)

    fill_default_value(
        content,
        chain=request.path_params['chain'],
        network=request.path_params['network'],
    )

    return OpenAPIResponse(content)


async def init_app(app: Application):
    swagger = Router()
    swagger.add_route('/schema/{chain}/{network}', custom_schema, include_in_schema=False)

    create_swagger(apispec, router=swagger)
    app.mount('/', swagger)
