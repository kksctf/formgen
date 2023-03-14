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
            field_name=field.name,
            field=field,
            field_name_root=field_name_root,
        )

        label = LabelTag(class_="col-2 col-form-label", label=field.name)
        div0 = DivTag(class_="col", tags=[input_body])
        div = DivTag(class_="form-group row", tags=[label, div0])
        tags.append(PTag(class_="my-1", tags=[div]))
    return Tags(tags)


def check_for_optional(annotation: type) -> bool:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin not in [typing.Union, types.UnionType]:
        return False

    if type(None) in args:
        return True

    return False


def get_input(
    model_type: Type[PydanticModel],
    model: PydanticModel | None,
    field_name: str,
    field: ModelField,
    field_name_root: str | None = None,
) -> Tag:
    ret = "fallback, "

    field_name = (field_name_root + "." if field_name_root else "") + field.alias
    field_last = field.alias
    value = getattr(model, field_last) if model and field_last in model.__fields_set__ else field.default
    origin = get_origin(field.annotation)
    args = get_args(field.annotation)
    is_optional = check_for_optional(field.annotation)

    if is_optional:  # TODO: do something with optional
        ret = f"OPTIONAL, {field.annotation = }, {field.sub_fields = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    if origin in [typing.Union, types.UnionType] and all(issubclass(arg, BaseModel) for arg in args):
        raw_opts: list[OptionTag] = []
        raw_divs: list = []

        for united_model in args:
            united_model: Type[BaseModel]
            model_name = united_model.__name__
            inner_form = generate_form_inner(
                model_type=united_model,
                model=value,
                field_name_root=field_name,
            )
            raw_opts.append(
                OptionTag(
                    value=model_name,
                    selected=False,
                ),
            )
            raw_divs.append(
                DivTag(
                    id=f"class-selector-forms-{ field_name }",
                    class_="form_class_selector_class",
                    tags=[inner_form],
                    extra_attrs={
                        "data-propname": field_name,
                        "data-ref": model_name,
                    },  # | attribs,
                ),
            )

        return Tags(
            [
                SelectTag(
                    name=field_name,
                    id=f"class-selector-{ field_name }",
                    class_="form-control form_class_selector form-select",
                    options=raw_opts,
                    extra_attrs={
                        "data-propname": field_name,
                    },  # | attribs,
                ),
                DivTag(
                    class_="form_class_selector_list",
                    tags=raw_divs,
                ),
            ],
        )

    if origin in [typing.Union, types.UnionType]:
        ret = f"GENERIC_UNION, {field.annotation = }, {field.sub_fields = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    if issubclass(field.annotation, Enum):
        enum: Type[Enum] = field.annotation
        members = enum._member_map_  # noqa: SLF001, W0212 # i know.

        return SelectTag(
            name=field_name,
            class_="form-select",
            options=[
                OptionTag(
                    value=str(enum_val),
                    selected=enum_val == value,
                )
                for enum_val in members.values()
            ],
        )

    if origin == list and issubclass((enum := args[0]), Enum):
        members = enum._member_map_  # noqa: SLF001, W0212 # i know.

        return SelectTag(
            name=field_name,
            class_="form-select form-select-multiple",
            options=[
                OptionTag(
                    value=str(enum_val),
                    selected=enum_val in value,
                )
                for enum_val in members.values()
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

    if origin == typing.Literal or issubclass(field.annotation, str):  # noqa: W0143
        out_tag = InputTag(
            class_="form-control",
            type_="text",
            name=field_name,
            placeholder=field.field_info.description or field_name,
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
