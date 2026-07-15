# pylint: disable=invalid-name
from typing import TypeVar
from pydantic import ConfigDict
from pydantic import BaseModel

INPUTTYPE = TypeVar("INPUTTYPE", bound=BaseModel)

DTO_EDGE_CONFIG = ConfigDict(
    frozen=True,
    use_enum_values=True,
    extra="forbid",
    arbitrary_types_allowed=True,
    kind="DTO",
)

DTO_CONFIG = ConfigDict(frozen=True, use_enum_values=True, extra="forbid", kind="DTO")
