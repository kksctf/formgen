# ruff: noqa: A003

from enum import Enum
from pydantic import BaseModel, Field

VAL = dict | list | str | bool | None


class Types(Enum):
    object = "object"
    string = "string"
    boolean = "boolean"
    integer = "integer"

    array = "array"
    class_ = "class"

    # custom types
    textarea = "textarea"
    html = "html"

    unknown = ""


class Formats(Enum):
    uuid = "uuid"
    datetime = "date-time"
    date = "date"
    time = "time"
    timedelta = "time-delta"
    binary = "binary"


class AdditionalProperty(BaseModel):
    type: Types
    format: Formats


class Property(BaseModel):
    title: str | None
    type: Types = Types.unknown

    format: Formats | None
    default: VAL

    any_of: list[dict[str, str]] | None = Field(alias="anyOf")

    additional_properties: AdditionalProperty | None = Field(alias="additionalProperties")

    enum: list[str] | None  # fake

    unique_items: bool | None = Field(alias="uniqueItems")

    const: str | None

    ref: str | None = Field(alias="$ref")

    all_of: list[dict[str, str]] | None = Field(alias="allOf")

    items: dict[str, str] | None

    @property
    def some_ref(self) -> str | None:
        all_of_resolve = self.all_of[0]["$ref"] if self.all_of and len(self.all_of) > 0 else None
        return self.ref or all_of_resolve or None

    @property
    def is_class(self) -> bool:
        return any([self.ref, self.all_of])


class Model(BaseModel):
    title: str
    type: Types

    description: str | None

    properties: dict[str, Property] = {}

    enum: list[str] | None

    required: list[str] = []

    definitions: dict[str, "Model"] = {}
