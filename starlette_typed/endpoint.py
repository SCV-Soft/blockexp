import functools
import inspect
from asyncio import iscoroutinefunction
from dataclasses import dataclass, field, is_dataclass
from inspect import Parameter
from traceback import TracebackException
from typing import Any
from typing import Optional, Callable, Type, Dict, TypeVar, Set, List, get_type_hints
from typing import cast

import typing_inspect
from requests import Request
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse

from .marshmallow import build_schema, Schema

T = TypeVar('T')


@dataclass
class Description:
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    input_headers: Optional[Schema] = None
    input_path: Optional[Schema] = None
    input_query: Optional[Schema] = None
    input_forms: Optional[Schema] = None
    input_body: Optional[Schema] = None
    output: Optional[Type[Response]] = None
    output_body: Optional[Schema] = None
    output_body_cls: Optional[Type] = None
    output_body_many: Optional[bool] = None
    output_type: Optional[Type] = None


def get_description(view_func: Callable) -> Optional[Description]:
    try:
        # noinspection PyUnresolvedReferences
        description = view_func.description
    except AttributeError:
        return None
    else:
        return cast(Description, description)


def typed_endpoint(*, tags: Set[str] = None):
    def wrapper(view_func: Callable):
        if not callable(view_func) or not iscoroutinefunction(view_func):
            raise TypeError("not async callable")

        module = inspect.getmodule(view_func)

        description = Description(
            summary=f"{module.__name__}.{view_func.__qualname__}",
            description=view_func.__doc__,
        )

        if tags:
            description.tags.update(tags)

        fill_description(view_func, description)

        view_func = build_new_view_func(view_func, description)
        view_func.description = description
        return view_func

    return wrapper


def fill_description(view_func: Callable, description: Description):
    annotations = get_parameters_annotations(view_func)

    unknown_names = set()
    return_annotation: Optional[Type] = None

    for name, cls in annotations.items():
        if (name == "request" or name == "_") and (cls == Request or issubclass(cls, Request)):
            pass
        elif name == "headers":
            description.input_headers = build_schema(cls, is_nested=False)
        elif name == "path":
            description.input_path = build_schema(cls, is_nested=False)
        elif name == "query":
            description.input_query = build_schema(cls, is_nested=False)
        elif name == "forms":
            description.input_forms = build_schema(cls, is_nested=False)
        elif name == "body":
            description.input_body = build_schema(cls, is_nested=True)
        elif name == "return":
            return_annotation = cls
        else:
            unknown_names.add(name)

    if return_annotation is not None:

        if issubclass(return_annotation, Response):
            description.output = return_annotation
        else:
            many = False

            if typing_inspect.is_generic_type(return_annotation):
                origin = typing_inspect.get_origin(return_annotation)
                if origin == List or origin == list:
                    tt, = typing_inspect.get_args(return_annotation)
                    return_annotation = tt
                    many = True
                else:
                    raise TypeError

            if is_dataclass(return_annotation):
                return_schema = build_schema(return_annotation, is_nested=True, many=many)
                description.output_body = return_schema
                description.output_body_cls = return_annotation
                description.output_body_many = many
            else:
                assert not many
                description.output_type = return_annotation

    if unknown_names:
        raise Exception(f"unexcepted arguments: {', '.join(unknown_names)}")


def get_parameters_annotations(view_func: Callable) -> Dict[str, Type]:
    raw_hints = {}

    signature = inspect.signature(view_func)
    for parameter in signature.parameters.values():  # type: Parameter
        name = parameter.name
        annotation = parameter.annotation

        if annotation is not Parameter.empty:
            raw_hints[name] = annotation

    # noinspection PyUnresolvedReferences
    ctx = view_func.__globals__

    hints = get_type_hints(view_func, ctx)
    return hints


def build_new_view_func(view_func: Callable, description: Description):
    func = view_func

    @functools.wraps(view_func)
    async def view_func(request: Request):
        try:
            kwargs = await parse_request(request, description)

            response = await func(request, **kwargs)

            return build_response(response, description)
        except Exception as exc:
            return build_error(request, exc)

    description.view_func = view_func
    return view_func


async def parse_request(request: Request, description: Description) -> dict:
    result = {}

    if description.input_headers is not None:
        result['headers'] = description.input_headers.load(dict(request.headers.items()))

    if description.input_path is not None:
        result['path'] = description.input_path.load(request.path_params)

    if description.input_query is not None:
        result['query'] = description.input_query.load(cast(dict, request.query_params))

    if description.input_forms is not None:
        result['forms'] = description.input_forms.load(cast(dict, await request.form()))

    if description.input_body is not None:
        result['body'] = description.input_body.load(await request.json())

    return result


def build_response(result: Any, description: Description) -> Response:
    if description.output is not None:
        assert isinstance(result, description.output)
        return result
    elif description.output_body is not None:
        return JSONResponse(description.output_body.dump(result))
    elif description.output_type is not None:
        assert isinstance(result, description.output_type)
        return JSONResponse(result)

    return result


def build_error(request: Request, exc: Exception) -> Response:
    tbe = TracebackException.from_exception(exc)

    return PlainTextResponse(
        status_code=500,
        content="".join(tbe.format()),
    )
