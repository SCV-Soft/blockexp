from typing import Callable, Set, Any, Dict, Type

# noinspection PyUnresolvedReferences
import apispec.core
import apispec.ext.marshmallow.common
import apispec.yaml_utils
from apispec import BasePlugin, APISpec
from apispec.exceptions import PluginMethodNotImplementedError
from apispec.ext.marshmallow import OpenAPIConverter, resolver as schema_name_resolver
from marshmallow import fields
from marshmallow.fields import Field
from starlette.responses import PlainTextResponse, JSONResponse

from starlette_typed.marshmallow import parse_type
from .endpoint import get_description

CONTENT_TEXT = PlainTextResponse.media_type
CONTENT_JSON = JSONResponse.media_type
CONTENT_FORM = "multipart/form-data"
CONTENT_URL = "application/x-www-form-urlencoded"

_apispec_modules = [
    apispec.core,
    apispec.ext.marshmallow.common,
    apispec.ext.marshmallow.openapi,
    apispec.yaml_utils,
]

_apispec_patched = False


def patch_apispec_orderdict():
    global _apispec_patched
    if not _apispec_patched:
        for module in _apispec_modules:
            try:
                module.OrderedDict
            except AttributeError:
                pass
            else:
                module.OrderedDict = dict

    _apispec_patched = True


def is_apispec_use_dict():
    return _apispec_patched


class TypedStarlettePlugin(BasePlugin):
    spec: APISpec
    openapi: OpenAPIConverter

    def init_spec(self, spec: APISpec):
        self.spec = spec
        self.openapi = OpenAPIConverter(spec.openapi_version, schema_name_resolver, spec)
        assert self.spec.openapi_version.major >= 3, self.spec.openapi_version

    def schema_helper(self, name, definition, **kwargs):
        """May return definition as a dict."""
        raise PluginMethodNotImplementedError

    def parameter_helper(self, parameter, **kwargs):
        """May return parameter component description as a dict."""
        func: Callable = kwargs.pop("func")
        description = get_description(func)
        raise PluginMethodNotImplementedError

    def response_helper(self, response, **kwargs):
        func: Callable = kwargs.pop("func")
        description = get_description(func)
        raise PluginMethodNotImplementedError

    def operation_helper(self, path=None, operations=None, **kwargs):
        http_method: Set[str] = kwargs.pop("http_method")
        func: Callable = kwargs.pop("func")
        description = get_description(func)
        if description is None:
            return

        operation = operations.setdefault(http_method, {})

        if description.summary is not None:
            operation["summary"] = description.summary

        if description.description is not None:
            operation["description"] = description.description

        if description.tags:
            operation["tags"] = list(description.tags)

        if description.input_query or description.input_path:
            parameters = operation.setdefault("parameters", [])

            if description.input_path:
                parameters.append({"in": "path", "schema": description.input_path})

            if description.input_query:
                parameters.append({"in": "query", "schema": description.input_query})

        if description.input_body or description.input_forms:
            request_content = operation.setdefault("requestBody", {}).setdefault("content", {})

            if description.input_body:
                request_content[CONTENT_JSON] = {"schema": description.input_body}

            if description.input_forms:
                # TODO: support binary format
                # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#media-type-object
                request_content[CONTENT_FORM] = {"schema": description.input_forms}

        if description.output or description.output_body or description.output_type:
            responses = operation.setdefault("responses", {})

            response: Dict[str, Any] = responses.setdefault(
                200,
                {
                    "description": "",
                    "content": {},
                }
            )

            response_content = response["content"]

            if description.output:
                media_type = description.output.media_type
                assert media_type, description.output
                if media_type == CONTENT_JSON:
                    response_content[media_type] = {"schema": self._convert_field(fields.Raw())}
                elif media_type == CONTENT_TEXT:
                    response_content[media_type] = {"schema": self._convert_field(fields.String())}

            if description.output_body:
                response_content[CONTENT_JSON] = {"schema": description.output_body}

            if description.output_type:
                response_content[CONTENT_JSON] = {"schema": self._convert_type(description.output_type)}

        # TODO: error codes

    def _convert_field(self, field: Field) -> dict:
        return self.openapi.field2property(field)

    def _convert_type(self, cls: Type) -> dict:
        return self._convert_field(parse_type(cls))
