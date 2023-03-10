from dataclasses import dataclass, field, asdict


@dataclass
class Tag:
    def __str__(self) -> str:
        return ""


@dataclass
class Tags(Tag):
    tags: list[Tag] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(map(str, self.tags))


@dataclass
class DummyTag(Tag):
    raw: str

    def __str__(self) -> str:
        return self.raw


@dataclass
class HTMLTag(Tag):
    id: str = ""  # noqa: A003 # it's ok
    class_: str = ""
    title: str = ""

    hidden: bool | None = None

    style: list[str] = field(default_factory=list)

    extra_attrs: dict[str, str | None] = field(default_factory=dict)

    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "class_":
                return "class"
            case "extra_attrs":
                return None
        return value_name

    @property
    def full_attrs(self) -> str:  # dict[str, str]:
        raw_full_attrs: dict[str, object | str | None]
        raw_full_attrs = asdict(self)
        raw_full_attrs = {ni: v for i, v in raw_full_attrs.items() if (ni := self.alias(i))}
        raw_full_attrs |= self.extra_attrs

        full_attrs: list[str] = []
        for attr_name, attr_value in raw_full_attrs.items():
            if attr_value is None:
                continue

            if not isinstance(attr_value, bool) and not attr_value:
                continue

            match attr_value:
                case list():
                    full_attrs.append(f'{attr_name}="{" ".join(attr_value)}"')
                case bool():
                    if attr_value:
                        full_attrs.append(f"{attr_name}")
                case _:
                    full_attrs.append(f'{attr_name}="{attr_value}"')

        return " ".join(full_attrs)


@dataclass
class DivTag(HTMLTag, Tags):
    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "tags":
                return None
        return HTMLTag.alias(self, value_name)

    def __str__(self) -> str:
        inner_tags = Tags.__str__(self)
        return f"<div {self.full_attrs}>\n{inner_tags}\n</div>"


@dataclass
class PTag(DivTag):
    def __str__(self) -> str:
        inner_tags = Tags.__str__(self)
        return f"<p {self.full_attrs}>\n{inner_tags}\n</p>"


@dataclass
class BaseInput(HTMLTag):
    type_: str = ""
    name: str = ""
    value: str = ""
    disabled: bool | None = None

    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "type_":
                return "type"
        return super().alias(value_name)

    def __str__(self) -> str:
        raise NotImplementedError


@dataclass
class InputTag(BaseInput):
    placeholder: str = ""

    checked: bool | None = None

    def __str__(self) -> str:
        return f"<input {self.full_attrs}>"


@dataclass
class TextareaTag(BaseInput):
    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "value":
                return None
        return super().alias(value_name)

    def __str__(self) -> str:
        return f"<textarea {self.full_attrs}>{self.value}</textarea>"


@dataclass
class ButtonTag(BaseInput):
    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "value":
                return None
        return super().alias(value_name)

    def __str__(self) -> str:
        return f"<button {self.full_attrs}>{self.value}</button>"


@dataclass
class OptionTag(HTMLTag):
    value: str = ""
    selected: bool | None = None

    def __str__(self) -> str:
        return f"<option {self.full_attrs}>{self.value}</option>"


@dataclass
class SelectTag(HTMLTag):
    options: list[OptionTag] = field(default_factory=list)
    multiple: bool | None = None

    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "options":
                return None
        return super().alias(value_name)

    def __str__(self) -> str:
        options = "\n".join(map(str, self.options))
        return f"<select {self.full_attrs}>{options}</select>"


@dataclass
class LabelTag(HTMLTag):
    label: str = ""

    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "label":
                return None
        return super().alias(value_name)

    def __str__(self) -> str:
        return f"<label {self.full_attrs}>{self.label}</label>"


@dataclass
class FormTag(HTMLTag, Tags):
    def alias(self, value_name: str) -> str | None:
        match value_name:
            case "tags":
                return None
        return super().alias(value_name)

    def __str__(self) -> str:
        inner_tags = Tags.__str__(self)
        return f"<form {self.full_attrs}>\n{inner_tags}\n</form>"
