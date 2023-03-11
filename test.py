import datetime
from enum import Enum
from typing import Literal
import uuid
import pytest
from pydantic import BaseModel, Field, validator


class BaseSubModel(BaseModel):
    classtype: Literal["BaseSubModel"] = "BaseSubModel"


class BaseSubModelN1(BaseSubModel):
    classtype: Literal["BaseSubModelN1"] = "BaseSubModelN1"

    integer: int
    initialized_integer: int = 1337


class BaseSubModelN2(BaseSubModel):
    classtype: Literal["BaseSubModelN2"] = "BaseSubModelN2"

    integer: int
    initialized_integer: int = 1337

    initialized_string: str = "l33t"


class Enumed(str, Enum):
    val1 = "val1"
    val2 = "val2"
    val3 = "val3"


class TestModel(BaseModel):
    some_aliased: str = Field(default="keke", alias="someAliased")

    some_id: uuid.UUID = Field(default_factory=uuid.uuid4)

    some_str: str
    some_initialized_str: str = "initializer"

    sub: BaseSubModel | BaseSubModelN1 | BaseSubModelN2
    sub_1: BaseSubModelN1

    description: str
    description_html: str

    some_dict: dict[uuid.UUID, datetime.datetime] = {}

    some_bool: bool
    some_initialized_bool: bool = True

    some_initialized_list: list[str] = []
    some_unitialized_list: list[str]

    some_WTF_list: list[str] | None = None  # noqa: N815

    some_enum: Enumed = Field()
    some_enum_with_def: Enumed = Field(default=Enumed.val2, description="kekeke")

    some_enum_list: list[Enumed] = Field(default=[Enumed.val1, Enumed.val3], description="ehehehe")

    united: str | bool = False

    # it's time for crazy solution.
    # Taken from https://github.com/samuelcolvin/pydantic/issues/619#issuecomment-635784061
    @validator("sub", pre=True)
    def validate_scoring(cls, value: object) -> BaseModel:  # noqa: E0213, N805
        if isinstance(value, BaseModel):
            return value
        if not isinstance(value, dict):
            raise ValueError("value must be dict")  # noqa: TRY004 # no,

        match value.get("classtype"):
            case "BaseSubModel":
                return BaseSubModel(**value)
            case "BaseSubModelN1":
                return BaseSubModelN1(**value)
            case "BaseSubModelN2":
                return BaseSubModelN2(**value)
            case classtype:
                raise ValueError(f"Unkonwn classtype {classtype}")
