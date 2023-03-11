import types
import typing
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Type, TypeVar, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import ModelField

from .tags import (
    ButtonTag,
    DivTag,
    DummyTag,
    FormTag,
    InputTag,
    LabelTag,
    OptionTag,
    PTag,
    SelectTag,
    Tag,
    Tags,
    TextareaTag,
)

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


def generate_form(
    model_type: Type[PydanticModel],
    model: PydanticModel | None = None,
    form_id: str = "",
    form_class: str = "",
) -> Tag:
    form_body = generate_form_inner(
        model_type=model_type,
        model=model,
    )

    return FormTag(
        id=form_id,
        class_=form_class,
        tags=[
            form_body,
            ButtonTag(
                class_="btn btn-primary btn-block mt-3",
                type_="submit",
                value="submit",
                extra_attrs={"accesskey": "s"},
            ),
        ],
    )


def generate_form_inner(
    model_type: Type[PydanticModel],
    model: PydanticModel | None = None,
    field_name_root: str | None = None,
) -> Tag:
    tags = []

    for field in model_type.__fields__.values():
        input_body = get_input(
            model_type=model_type,
            model=model,
            field_name=(field_name_root + "." if field_name_root else "") + field.name,
            field=field,
        )

        label = LabelTag(class_="col-2 col-form-label", label=field.name)
        div0 = DivTag(class_="col", tags=[input_body])
        div = DivTag(class_="form-group row", tags=[label, div0])
        tags.append(PTag(class_="my-1", tags=[div]))
    return Tags(tags)


def get_input(
    model_type: Type[PydanticModel],
    model: PydanticModel | None,
    field_name: str,
    field: ModelField,
) -> Tag:
    ret = "fallback, "

    field_name = field.alias
    value = getattr(model, field_name) if model and field_name in model.__fields_set__ else field.default
    origin = get_origin(field.annotation)
    args = get_args(field.annotation)

    if origin in [typing.Union, types.UnionType]:
        ret = f"UNION, {field.annotation = }, {field.sub_fields = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    if origin == typing.Literal or issubclass(field.annotation, str):  # noqa: W0143
        out_tag = InputTag(
            class_="form-control",
            type_="text",
            name=field_name,
            placeholder=field_name,
            value=str(value),
            # extra_attrs=attribs,
        )
        if origin == typing.Literal:  # noqa: W0143
            out_tag.disabled = True
        return out_tag

    if issubclass(field.annotation, bool):
        return InputTag(
            class_="my-2 form-check-input",
            type_="checkbox",
            name=field_name,
            checked=bool(value),
            # extra_attrs=attribs,
        )

    if issubclass(field.annotation, int):
        return InputTag(
            type_="number",
            name=field_name,
            value=str(value),
            # extra_attrs=attribs,
        )

    if origin == list and issubclass((enum := args[0]), Enum):
        members = enum._member_map_  # noqa: SLF001, W0212 # i know.

        return SelectTag(
            class_="form-select form-select-multiple",
            options=[
                OptionTag(
                    value=enum_val,
                    selected=enum_val in value,
                )
                for enum_val in members
            ],
            multiple=True,
        )

    if origin == list:
        ret = f"LIST, {field.annotation = }, {field.sub_fields = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    if origin == dict:
        ret = f"DICT, {field.annotation = }, {field.sub_fields = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    if issubclass(field.annotation, Enum):
        enum: Type[Enum] = field.annotation
        members = enum._member_map_  # noqa: SLF001, W0212 # i know.

        return SelectTag(
            class_="form-select",
            options=[
                OptionTag(
                    value=enum_val,
                    selected=enum_val == value,
                )
                for enum_val in members
            ],
        )

    if issubclass(field.annotation, BaseModel):
        return generate_form_inner(
            model_type=field.annotation,
            model=value,
            field_name_root=field_name,
        )

    ret += f"{field.annotation = }, {field.sub_fields = }"
    ret = ret.replace("<", "&lt;").replace(">", "&gt;")
    ret = f"<pre> {ret} </pre>"
    return DummyTag(ret)
