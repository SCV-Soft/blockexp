"""
https://github.com/lovasoa/marshmallow_dataclass
"""

import dataclasses
import enum
import typing
from weakref import WeakKeyDictionary

import marshmallow
import marshmallow_enum as mm_fields2
import typing_inspect
from marshmallow import fields as mm_fields
from marshmallow.schema import Schema, BaseSchema

__all__ = ['schema', 'Schema', 'build_schema']

# noinspection PyRedeclaration
Schema: typing.Type[BaseSchema]


def build_schema(cls: typing.Type, *, is_nested: bool, many=False) -> Schema:
    # TODO: is_nested
    return schema(cls, many=many)


def schema(cls: typing.Type, *, name=None, only=None, exclude=(), many=False, context=None,
           load_only=(), dump_only=(), partial=False, unknown=None) -> Schema:
    # noinspection PyShadowingNames
    schema = load_schema(cls, name=name)
    return schema(
        only=only,
        exclude=exclude,
        many=many,
        context=context,
        load_only=load_only,
        dump_only=dump_only,
        partial=partial,
        unknown=unknown,
    )


SCHEMA_MAPPING = WeakKeyDictionary()


def load_schema(cls: typing.Type, *, name: str = None) -> typing.Type[Schema]:
    schema = SCHEMA_MAPPING.get(cls)
    if schema is None:
        schema = SCHEMA_MAPPING[cls] = parse_dataclass(cls, name=name)

    return schema


def parse_dataclass(cls: typing.Type, name: str = None) -> typing.Type[Schema]:
    if not dataclasses.is_dataclass(cls):
        raise TypeError

    hints = typing.get_type_hints(cls)
    # noinspection PyDataclass
    for field in dataclasses.fields(cls):
        field.type = hints[field.name]

    # noinspection PyDataclass
    cls_dict = {
        field.name: parse_field(field)
        for field in dataclasses.fields(cls)
    }

    if 'Meta' not in cls_dict:
        cls_dict['Meta'] = type('Meta', (), {'ordered': True})

    safe_name = {
        name: name.rstrip('_')
        for name in cls_dict
        if name.endswith('_')
    }

    class BaseSchema(Schema):
        @marshmallow.post_load
        def make_dataclass(self, data, *, many, partial):
            return cls(**data)

        if safe_name:
            @marshmallow.pre_load
            def prepare_dataclass(self, data, *, many, partial):
                for safe, unsafe in safe_name.items():
                    if unsafe in data:
                        data[safe] = data.pop(unsafe)

                return data

            @marshmallow.post_dump
            def make_object(self, data, *, many, partial):
                return {safe_name.get(key, key): value
                        for key, value in data.items()}

    schema_cls = type(name or cls.__name__, (BaseSchema,), cls_dict)
    return typing.cast(typing.Type[Schema], schema_cls)


def unwrap_optional(cls: typing.Type) -> typing.Type:
    assert typing_inspect.is_optional_type(cls)
    if not typing_inspect.is_union_type(cls):
        raise NotImplementedError

    origin_args = typing_inspect.get_args(cls)

    selected_tt = None
    for tt in origin_args:
        if tt is type(None):
            continue
        elif selected_tt is None:
            selected_tt = tt
        else:
            raise TypeError

    return selected_tt


def update_missing(metadata: typing.Optional[dict] = None,
                   dc_field: typing.Optional[dataclasses.Field] = None,
                   default=marshmallow.missing) -> dict:
    if metadata is None:
        metadata = {}

    if dc_field is not None:
        if dc_field.default_factory is not dataclasses.MISSING:
            default = dc_field.default_factory
        elif dc_field.default is not dataclasses.MISSING:
            default = dc_field.default

    metadata.setdefault('required', default is marshmallow.missing)
    metadata.setdefault('default', default)
    metadata.setdefault('missing', default)
    return metadata


def parse_field(dc_field: dataclasses.Field) -> mm_fields.Field:
    mm_field = parse_type(dc_field.type, dict(dc_field.metadata), dc_field)

    description = dc_field.metadata.get('description')
    if description is not None:
        mm_field.metadata['description'] = description

    return mm_field


def parse_type(cls: typing.Type,
               metadata: typing.Optional[dict] = None,
               dc_field: typing.Optional[dataclasses.Field] = None) -> mm_fields.Field:
    try:
        # noinspection PyUnresolvedReferences
        cls = cls.__supertype__
    except AttributeError:
        pass

    if metadata is not None and 'marshmallow_field' in metadata:
        return metadata.get('marshmallow_field')
    elif typing_inspect.is_generic_type(cls):
        origin = typing_inspect.get_origin(cls)
        if origin == typing.List or origin == list:
            tt, = typing_inspect.get_args(cls)
            return mm_fields.List(
                parse_type(tt),
                **update_missing(metadata, dc_field),
            )
        elif origin == typing.Dict or origin == dict:
            tk, tv = typing_inspect.get_args(cls)
            return mm_fields.Mapping(
                parse_type(tk),
                parse_type(tv),
                **update_missing(metadata, dc_field),
            )
        elif origin == typing.Tuple or origin == tuple:
            tts = typing_inspect.get_args(cls)
            # TODO: handle ecplise?
            raise NotImplementedError
        elif origin == typing.Set or origin == set:
            tt, = typing_inspect.get_args(cls)
            return mm_fields.List(
                parse_type(tt),
                **update_missing(metadata, dc_field),
            )
        else:
            raise TypeError(f'invalid type: {cls!r}')
    elif typing_inspect.is_optional_type(cls):
        tt = unwrap_optional(cls)
        return parse_type(tt, update_missing(metadata, dc_field, default=None))
    elif dataclasses.is_dataclass(cls):
        return mm_fields.Nested(
            parse_dataclass(cls),
            **update_missing(metadata, dc_field),
        )
    elif type(cls) is enum.EnumMeta:
        return mm_fields2.EnumField(
            cls,
            **update_missing(metadata, dc_field),
        )
    elif isinstance(cls, type) and (cls == dict or issubclass(cls, dict)):
        return mm_fields.Mapping(
            **update_missing(metadata, dc_field),
        )
    elif cls == typing.Any:
        return mm_fields.Raw(
            **update_missing(metadata, dc_field),
        )
    else:
        mm_field_type = BaseSchema.TYPE_MAPPING.get(cls, mm_fields.Raw)
        if mm_field_type is mm_fields.Raw:
            print(repr(cls), dc_field)
            raise TypeError(f'invalid type: {cls!r}')

        return mm_field_type(**update_missing(metadata, dc_field))
