# ruff: noqa: PLR0911, PLR0913

from dataclasses import dataclass
from typing import Any
from ..tags import (
    ButtonTag,
    DivTag,
    DummyTag,
    InputTag,
    LabelTag,
    OptionTag,
    PTag,
    SelectTag,
    Tag,
    Tags,
    TextareaTag,
    FormTag,
)
from .schema import Model, Property, AdditionalProperty, Types, Formats, VAL


@dataclass
class Context:
    values: dict[str, "VAL | Context"]
    attributes: dict[str, "str | Context"]
    overrides: dict[str, "str | Context"]


def get_input(
    prop_name: str,
    prop: Property,
    attribs: dict,
    schema: Model,
    value: VAL = None,
    type_override: Types | None = None,
) -> Tag:
    title = prop.title or prop_name
    input_type: Types = type_override if type_override else prop.type
    inner_value = (
        prop.const
        if prop.const
        else (value if value is not None else (prop.default if prop.default is not None else ""))
    )

    ret = ""
    match input_type:
        case Types.string:
            return InputTag(
                class_="form-control",
                type_="text",
                name=prop_name,
                placeholder=title,
                value=str(inner_value),
                extra_attrs=attribs,
            )
        case Types.integer:
            return InputTag(
                type_="number",
                name=prop_name,
                value=str(inner_value),
                extra_attrs=attribs,
            )
        case Types.boolean:
            return InputTag(
                class_="my-2 form-check-input",
                type_="checkbox",
                name=prop_name,
                extra_attrs=attribs,
                checked=bool(inner_value),
            )
        case Types.textarea:
            return TextareaTag(
                type_="text",
                name=prop_name,
                value=str(inner_value),
                extra_attrs=attribs,
            )
        case Types.array:
            if not prop.items:
                return DummyTag(f"ARRAY_BROKE: {prop}")

            if "$ref" in prop.items:
                ref: str = prop.items["$ref"].split("/")[-1]
                if ref not in schema.definitions:
                    return DummyTag(f"_NO_REF_IN_DEF_{ ref }_; {prop}")

                defin = schema.definitions[ref]
                defin.definitions = schema.definitions

                if enum := defin.enum:
                    default = prop.default
                    return SelectTag(
                        class_="form-select form-select-multiple",
                        options=[
                            OptionTag(
                                value=enum_val,
                                selected=enum_val == default,
                            )
                            for enum_val in enum
                        ],
                        multiple=True,
                    )
            else:
                return DummyTag("NOT SUPPORTED_ARRAY")

        case Types.html:
            # FIXME: make this safe!
            safe_inner_value = DummyTag(str(inner_value))
            inp = InputTag(
                class_="form-control",
                type_="hidden",
                name=prop_name,
                placeholder=title,
                value=str(inner_value),
                disabled=True,
                extra_attrs=attribs,
            )
            btn = ButtonTag(
                class_="btn btn-primary",
                type_="button",
                value="Display server MD preview",
                extra_attrs={
                    "data-bs-toggle": "collapse",
                    "data-bs-target": f"#html-collapse-{ prop_name }",
                    "aria-expanded": "false",
                    "aria-controls": f"html-collapse-{ prop_name }",
                }
                | attribs,
            )
            div0 = DivTag(
                tags=[safe_inner_value],
            )
            div = DivTag(
                id=f"html-collapse-{ prop_name }",
                class_="collapse",
                tags=[div0],
            )
            return Tags([inp, btn, div])
        case Types.class_ if prop.any_of is not None:
            raw_opts: list[OptionTag] = []
            raw_divs: list = []

            for raw_ref in prop.any_of:
                ref: str = raw_ref["$ref"].split("/")[-1]
                if ref not in schema.definitions:
                    raw_opts.append(OptionTag(value=f"WTF WTF: {raw_ref}"))
                    continue

                defin = schema.definitions[ref]
                defin.definitions = schema.definitions
                selected = (
                    inner_value["classtype"] == ref
                    if isinstance(inner_value, dict) and "classtype" in inner_value
                    else False
                )

                inner_form = generate_form_inner(
                    schema=defin,
                    prop_name_root=prop_name,
                )
                raw_opts.append(
                    OptionTag(
                        value=ref,
                        selected=selected,
                    ),
                )
                raw_divs.append(
                    DivTag(
                        id=f"class-selector-forms-{ prop_name }",
                        class_="form_class_selector_class",
                        tags=[inner_form],
                        extra_attrs={
                            "data-propname": prop_name,
                            "data-ref": ref,
                        }
                        | attribs,
                    ),
                )

            return Tags(
                [
                    SelectTag(
                        id=f"class-selector-{ prop_name }",
                        class_="form-control form_class_selector form-select",
                        options=raw_opts,
                        extra_attrs={
                            "data-propname": prop_name,
                        }
                        | attribs,
                    ),
                    DivTag(
                        class_="form_class_selector_list",
                        tags=raw_divs,
                    ),
                ],
            )
        case _:
            raw_ref = prop.some_ref
            if raw_ref is None:
                return DummyTag(f"_NOT_KNOWN_TYPE_{ input_type }_; {prop}")
            ref: str = raw_ref.split("/")[-1]
            if ref not in schema.definitions:
                return DummyTag(f"_NO_REF_IN_DEF_{ ref }_; {prop}")

            defin = schema.definitions[ref]
            defin.definitions = schema.definitions

            if enum := defin.enum:
                default = prop.default
                return SelectTag(
                    class_="form-select",
                    options=[
                        OptionTag(
                            value=enum_val,
                            selected=enum_val == default,
                        )
                        for enum_val in enum
                    ],
                )

            return generate_form_inner(
                schema=defin,
                prop_name_root=prop_name,
            )

    return DummyTag(ret)


def generate_form_inner(
    schema: Model,
    values: dict | None = None,
    overrides: dict | None = None,
    attribs: dict | None = None,
    prop_name_root: str | None = None,
) -> Tag:
    values = values or {}
    overrides = overrides or {}
    attribs = attribs or {}

    tags = []
    # {% set args = {
    #     "prop_name": (prop_name_root + "." if prop_name_root else "") + prop_name,
    #     "prop": prop,
    #     "attribs": attribs.get(prop_name, []),
    #     'schema': schema,
    #     "value": values.get(prop_name, None),
    #     'type_override': overrides.get(prop_name, None)
    # } %}
    # {% if prop_name in schema["required"] and isinstance(args["attribs"], [].__class__) %}
    #     {% set _ = args.update(attribs=args["attribs"] + ["required"]) %}
    # {% endif %}
    for prop_name, prop in schema.properties.items():
        input_body = get_input(
            prop_name=(prop_name_root + "." if prop_name_root else "") + prop_name,
            prop=prop,
            attribs=attribs.get(prop_name, {}),
            schema=schema,
            value=values.get(prop_name, None),
            type_override=overrides.get(prop_name, None),
        )

        label = LabelTag(class_="col-2 col-form-label", label=prop.title or prop_name)
        div0 = DivTag(class_="col", tags=[input_body])
        div = DivTag(class_="form-group row", tags=[label, div0])
        tags.append(PTag(class_="my-1", tags=[div]))
    return Tags(tags)


def generate_form(
    raw_schema: dict,
    form_id: str = "",
    form_class: str = "",
    values: dict | None = None,
    overrides: dict | None = None,
    attribs: dict | None = None,
) -> Tag:
    values = values or {}
    overrides = overrides or {}
    attribs = attribs or {}

    parsed_schema = Model.parse_obj(raw_schema)

    form_body = generate_form_inner(
        schema=parsed_schema,
        values=values,
        overrides=overrides,
        attribs=attribs,
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
