import types
import typing
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Self, Type, TypeVar, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core._pydantic_core import PydanticUndefined

from ..tags import (
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


class FieldType(Enum):
    UNKNOWN = 0

    NESTED_MODEL = auto()

    NUMBER = auto()
    BOOLEAN = auto()
    STRING = auto()

    LIST = auto()
    DICT = auto()

    ENUM = auto()
    ENUM_LIST = auto()

    LITERAL = auto()

    GENERIC_UNION = auto()

    NESTED_UNION = auto()

    # SPECIAL TYPES
    TEXTAREA = auto()
    HTML = auto()

    @classmethod
    def resolve_type(cls: type[Self], field: FieldInfo) -> Self:
        if not field.annotation:
            return cls.UNKNOWN

        origin = get_origin(field.annotation)
        args = get_args(field.annotation)

        if origin in [typing.Union, types.UnionType] and all(issubclass(arg, BaseModel) for arg in args):
            return cls.NESTED_UNION

        if origin in [typing.Union, types.UnionType]:
            return cls.GENERIC_UNION

        if origin == typing.Literal:  # noqa: W0143
            return cls.LITERAL

        if issubclass(field.annotation, Enum):
            return cls.ENUM

        if origin == list and issubclass(args[0], Enum):
            return cls.ENUM_LIST

        if origin == dict:
            return cls.DICT

        if origin == list:
            return cls.LIST

        if issubclass(field.annotation, str) or issubclass(field.annotation, uuid.UUID):  # noqa: W0143
            return cls.STRING

        if issubclass(field.annotation, bool):
            return cls.BOOLEAN

        if issubclass(field.annotation, int):
            return cls.NUMBER

        if issubclass(field.annotation, BaseModel):
            return cls.NESTED_MODEL

        return cls.UNKNOWN


@dataclass(frozen=True)
class Context:
    attributes: dict[str, str | None] = field(default_factory=dict)
    override: FieldType = FieldType.UNKNOWN


@dataclass(frozen=True)
class Contexts:
    contexts: dict[str, "Context | Contexts"] = field(default_factory=dict)


def generate_form(
    model_type: Type[PydanticModel],
    model: PydanticModel | None = None,
    form_id: str = "",
    form_class: str = "",
    readonly: bool = False,
    disabled_fields: list[str] | None = None,
    contexts: Contexts = Contexts(),
) -> Tag:
    form_body = generate_form_inner(
        model_type=model_type,
        model=model,
        readonly=readonly,
        disabled_fields=disabled_fields,
        contexts=contexts,
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
    readonly: bool = False,
    disabled_fields: list[str] | None = None,
    contexts: Contexts = Contexts(),
) -> Tag:
    tags = []
    disabled_fields = disabled_fields or []

    for field_name, field in (model if model else model_type).model_fields.items():
        input_body = get_input(
            model_type=model_type,
            model=model,
            field_name=field_name,
            field=field,
            field_name_root=field_name_root,
            readonly=readonly,
            disabled_fields=disabled_fields,
            context=contexts.contexts.get(field_name, None),
        )

        fancy_field_name = field_name.replace("_", " ").capitalize()
        label = LabelTag(class_="col-2 col-form-label", label=fancy_field_name)
        div0 = DivTag(class_="col", tags=[input_body])

        _div_id_p_0 = field_name_root + "." if field_name_root else ""
        _dir_id_p_1 = field.alias or field_name
        div_id = ("div_" + _div_id_p_0 + _dir_id_p_1).replace(".", "__")

        div = DivTag(class_="form-group row", tags=[label, div0], id=div_id)
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
    field: FieldInfo,
    field_name_root: str | None = None,
    readonly: bool = False,
    disabled_fields: list[str] | None = None,
    context: Context | Contexts | None = None,
) -> Tag:
    ret = "fallback, "
    disabled_fields = disabled_fields or []

    if not field.annotation:
        ret = f"EMPTY field.annotation, {field.annotation = }, {field = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    field_last = field.alias or field_name
    field_name = (field_name_root + "." if field_name_root else "") + field_last

    value = field.default
    try:
        value = getattr(model, field_last) if model else field.default
    except AttributeError as ex:
        pass  # TODO: fix that.

    origin = get_origin(field.annotation)
    args = get_args(field.annotation)
    is_optional = check_for_optional(field.annotation)
    disabled = True if readonly or (field_name in disabled_fields) else None
    extra_attrs = context.attributes if isinstance(context, Context) else {}
    field_type = context.override if isinstance(context, Context) else FieldType.UNKNOWN

    # fix pydantic undefined value
    if value == PydanticUndefined:
        value = None

    if is_optional:  # TODO: do something with optional
        ret = f"OPTIONAL, {field.annotation = }, {field = }"
        ret = ret.replace("<", "&lt;").replace(">", "&gt;")
        ret = f"<pre> {ret} </pre>"
        return DummyTag(ret)

    if field_type == FieldType.UNKNOWN:
        field_type = FieldType.resolve_type(field)

    match field_type:
        case FieldType.NESTED_MODEL:
            if not issubclass(field.annotation, BaseModel):
                raise Exception("impossible")  # make typing happy

            return generate_form_inner(
                model_type=field.annotation,
                model=value,
                field_name_root=field_name,
                readonly=readonly,
                disabled_fields=disabled_fields,
                contexts=context if isinstance(context, Contexts) else Contexts(),
            )

        case FieldType.NUMBER:
            return InputTag(
                type_="number",
                name=field_name,
                value=str(value or 0),
                disabled=disabled,
                extra_attrs=extra_attrs,
            )

        case FieldType.BOOLEAN:
            return InputTag(
                class_="my-2 form-check-input",
                type_="checkbox",
                name=field_name,
                checked=bool(value or False),
                disabled=disabled,
                extra_attrs=extra_attrs,
            )

        case FieldType.STRING:
            return InputTag(
                class_="form-control",
                type_="text",
                name=field_name,
                placeholder=field.description or field_name,
                value=str(value or ""),
                disabled=disabled,
                extra_attrs=extra_attrs,
            )

        case FieldType.LIST:
            ret = f"LIST, {field.annotation = }, {get_args(field.annotation) = }"
            ret = ret.replace("<", "&lt;").replace(">", "&gt;")
            ret = f"<pre> {ret} </pre>"
            return DummyTag(ret)

        case FieldType.DICT:
            ret = f"DICT, {field.annotation = }, {get_args(field.annotation) = }"
            ret = ret.replace("<", "&lt;").replace(">", "&gt;")
            ret = f"<pre> {ret} </pre>"
            return DummyTag(ret)

        case FieldType.ENUM:
            if not issubclass(field.annotation, Enum):
                raise Exception("impossible")  # make typing happy

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
                disabled=disabled,
                extra_attrs=extra_attrs,
            )

        case FieldType.ENUM_LIST:
            if not issubclass((enum := args[0]), Enum):
                raise Exception("impossible")  # make typing happy

            members = enum._member_map_  # noqa: SLF001, W0212 # i know.

            return SelectTag(
                name=field_name,
                class_="form-select form-select-multiple",
                options=[
                    OptionTag(
                        value=str(enum_val),
                        selected=((enum_val in value) if value else False),
                    )
                    for enum_val in members.values()
                ],
                disabled=disabled,
                multiple=True,
                extra_attrs=extra_attrs,
            )

        case FieldType.LITERAL:
            return InputTag(
                class_="form-control",
                type_="text",
                name=field_name,
                placeholder=field.description or field_name,
                value=str(value),
                disabled=True,
                extra_attrs=extra_attrs,
            )

        case FieldType.GENERIC_UNION:
            ret = f"GENERIC_UNION, {field.annotation = }, {get_args(field.annotation) = }"
            ret = ret.replace("<", "&lt;").replace(">", "&gt;")
            ret = f"<pre> {ret} </pre>"
            return DummyTag(ret)

        case FieldType.NESTED_UNION:
            raw_opts: list[OptionTag] = []
            raw_divs: list = []

            for united_model in args:
                united_model: Type[BaseModel]
                model_name = united_model.__name__
                inner_form = generate_form_inner(
                    model_type=united_model,
                    model=value,
                    field_name_root=field_name,
                    contexts=context if isinstance(context, Contexts) else Contexts(),
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
                        }
                        | extra_attrs,
                    ),
                )

            return Tags(
                [
                    SelectTag(
                        name=field_name,
                        id=f"class-selector-{ field_name }",
                        class_="form-control form_class_selector form-select",
                        options=raw_opts,
                        disabled=disabled,
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

        case FieldType.TEXTAREA:
            return TextareaTag(
                class_="form-control",
                type_="text",
                name=field_name,
                value=str(value or ""),
                disabled=disabled,
                extra_attrs=extra_attrs,
            )

        case FieldType.HTML:
            return Tags(
                [
                    InputTag(
                        class_="form-control",
                        type_="hidden",
                        name=field_name,
                        placeholder=field.description or field_name,
                        value="",  # WTF: hack
                        disabled=True,
                        extra_attrs=extra_attrs,
                    ),
                    ButtonTag(
                        class_="btn btn-primary",
                        type_="button",
                        value="Display server MD preview",
                        extra_attrs={
                            "data-toggle": "collapse",
                            "data-target": f"#html-collapse-{ field_name }",
                            "aria-expanded": "false",
                            "aria-controls": f"#html-collapse-{ field_name }",
                        },
                    ),
                    DivTag(
                        id=f"html-collapse-{ field_name }",
                        class_="collapse",
                        tags=[
                            DivTag(
                                class_="card card-body",
                                tags=[DummyTag(str(value or ""))],
                            )
                        ],
                    )
                    # SelectTag(
                    #     name=field_name,
                    #     id=f"class-selector-{ field_name }",
                    #     class_="form-control form_class_selector form-select",
                    #     options=raw_opts,
                    #     disabled=disabled,
                    #     extra_attrs={
                    #         "data-propname": field_name,
                    #     },  # | attribs,
                    # ),
                    # DivTag(
                    #     class_="form_class_selector_list",
                    #     tags=raw_divs,
                    # ),
                ],
            )

    ret += f"{field.annotation = }, {field = }"
    ret = ret.replace("<", "&lt;").replace(">", "&gt;")
    ret = f"<pre> {ret} </pre>"
    return DummyTag(ret)
