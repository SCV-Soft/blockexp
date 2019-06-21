from typing import List, cast

from apispec import APISpec
from starlette.routing import BaseRoute
from starlette.schemas import BaseSchemaGenerator

from .apispec import is_apispec_use_dict


class TypedStarletteSchemaGenerator(BaseSchemaGenerator):
    def __init__(self, spec: APISpec):
        self.spec = spec

    @classmethod
    def _fix_deep(cls, obj):
        if isinstance(obj, list):
            return [cls._fix_deep(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: cls._fix_deep(value) for key, value in obj.items()}
        else:
            return obj

    def get_schema(self, routes: List[BaseRoute]):
        endpoints = self.get_endpoints(routes)
        for endpoint in endpoints:
            self.spec.path(
                path=endpoint.path,
                func=cast(dict, endpoint.func),
                http_method=cast(dict, endpoint.http_method),
            )

        schema = self.spec.to_dict()
        if not is_apispec_use_dict():
            schema = self._fix_deep(schema)

        return schema
