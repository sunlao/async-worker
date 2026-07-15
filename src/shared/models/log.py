from datetime import datetime
from time import perf_counter
from uuid import uuid4
from typing import Generic, Callable
from pydantic import Field, UUID4
from pydantic import BaseModel, SkipValidation
from shared.models.constants import Events, LogLevel, PathParts, Services, Environments
from shared.models.policy import DTO_CONFIG, DTO_EDGE_CONFIG, INPUTTYPE


class Config(BaseModel):
    """Config DTO used by Shared Logging package. Contains Time Objects to contain Stage
    at the edges"""

    model_config = DTO_EDGE_CONFIG
    Level: LogLevel
    Service: Services
    LogToFile: bool
    LogDirectory: str
    BackUpCount: int
    Environment: Environments
    Now: SkipValidation[Callable[[], datetime.now]]
    TimeCounter: SkipValidation[Callable[[], perf_counter]]
    UUID4: SkipValidation[Callable[[], uuid4]]


class Core(BaseModel):
    """Core logging DTO for all Services"""

    model_config = DTO_CONFIG
    Environment: Environments
    InputLevel: LogLevel
    Time: datetime
    TransactionID: UUID4
    Event: Events
    Message: str = Field(..., min_length=1, max_length=2000)


class Event(BaseModel, Generic[INPUTTYPE]):
    """Generic Logging Event DTO"""

    model_config = DTO_CONFIG
    Core: Core
    Event: INPUTTYPE


class LastPartTB(BaseModel):
    """DTO for returning data from internal function
    shared.log.helper.Error()._last_part_tb"""

    model_config = DTO_CONFIG
    Path: str
    FunctionName: str
    LineNo: int


class RelPathInput(BaseModel):
    """DTO for passing valid data to internal function
    shared.log.helper.Error()._rel_part_path"""

    model_config = DTO_CONFIG
    TBPath: str
    PathPart: PathParts


class TraceBackEvent(BaseModel):
    """DTO for Logging Trace Back Events"""

    model_config = DTO_CONFIG
    Exception: str
    ExceptionMessage: str
    LastTBFile: str
    LastTBFunction: str
    LastTBLineNo: int
    Last5TB: list[tuple[str, int, str]]
    TBCount: int


class CoreError(BaseModel):
    """Generic Logging Event DTO"""

    model_config = DTO_CONFIG
    Core: Core
    Error: TraceBackEvent


class EventError(BaseModel, Generic[INPUTTYPE]):
    """Generic Logging Event DTO"""

    model_config = DTO_CONFIG
    Core: Core
    Event: INPUTTYPE
    Error: TraceBackEvent
