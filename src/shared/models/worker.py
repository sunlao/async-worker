from datetime import datetime
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Tuple,
)
from redis.asyncio import Redis
from taskiq import AsyncBroker
from taskiq.abc.result_backend import AsyncResultBackend
from pydantic import BaseModel, Field, StrictStr, UUID4
from shared.models.constants import (
    ActionTypes,
    JobTypes,
    SourceTypes,
    TargetTypes,
)

from shared.models.log import Config, TraceBackEvent
from shared.models.policy import DTO_CONFIG, DTO_EDGE_CONFIG, INPUTTYPE


class AdminConfig(BaseModel):
    model_config = DTO_CONFIG
    Id: int = Field(..., gt=0)
    Name: StrictStr = Field(..., min_length=1)
    Cmd: str = Field("")
    ActionType: ActionTypes = Field(ActionTypes.EXE)
    Delay: int = Field(86400, ge=0)
    Retry: int = Field(3, ge=0)
    StartUp: bool = Field(False)
    RunOnce: bool = Field(True)
    RunNext: Optional[Tuple[int, ...]] = None


class AdminJobResult(BaseModel):
    model_config = DTO_CONFIG
    ExecutionId: UUID4
    Status: bool
    Code: int
    Message: str
    DurationMs: int = Field(ge=0)


class AdminEvent(BaseModel):
    model_config = DTO_CONFIG
    JobId: int = Field(gt=0)
    JobName: str
    ActionType: ActionTypes = Field(ActionTypes.EXE)
    Message: str
    Status: bool
    AdminResults: Optional[AdminJobResult] = None
    Start: datetime
    End: datetime
    DurationMs: int = Field(ge=0)


class SerializeInput(BaseModel):
    """Input DTO for the Avro Helper to be used by all connectors.
    Pass in Schema if available or helper will assign string to all data types"""

    model_config = DTO_CONFIG
    Rows: tuple[Mapping[str, object], ...]
    Name: str
    Schema: List[dict]


class BinaryOutput(BaseModel):
    """Output DTO for the Avro Helper to be used by all connectors"""

    model_config = DTO_CONFIG
    BytesSHA256: str
    BytesLen: int


class SerializeOutput(BaseModel):
    """Output DTO for the Avro Helper to be used by all connectors"""

    model_config = DTO_CONFIG
    AvroBytes: bytes
    SchemaJSON: Dict[str, Any]
    SchemaSHA256: str
    BytesSHA256: str
    BytesLen: int
    RowCount: int


class ExecutionConfig(BaseModel, Generic[INPUTTYPE]):
    model_config = DTO_CONFIG
    JobConfig: INPUTTYPE
    Start: datetime
    StartCounter: float


class HandleExecution(BaseModel, Generic[INPUTTYPE]):
    model_config = DTO_EDGE_CONFIG
    Event: Optional[INPUTTYPE]
    ErrorFlag: bool
    TraceBackEvent: Optional[TraceBackEvent]


class Health(BaseModel):
    model_config = DTO_CONFIG
    Complete: int
    Failed: int
    Retried: int
    Ongoing: int
    Queued: int


class LogCoreInput(BaseModel):
    model_config = DTO_CONFIG
    ConfigLog: Config
    TransactionID: UUID4
    Name: str


class MovementJobResult(BaseModel):
    model_config = DTO_CONFIG
    RowCount: int
    ActionType: ActionTypes
    LastHash: Optional[str] = None


class WorkerConfig(BaseModel):
    model_config = DTO_CONFIG
    StartUp: bool
    JobPath: str
    JobVersion: str
    DBMaxPool: int
    DataDir: str
    JobPath: str
    JobVersion: str
    GatePath: str


class MovementEvent(BaseModel):
    model_config = DTO_CONFIG
    JobId: int = Field(gt=0)
    JobName: str
    Status: bool
    Message: str
    Start: datetime
    End: datetime
    DurationMs: int = Field(ge=0)
    Source: str
    Result: Optional[MovementJobResult] = None


class MovementConfig(BaseModel):
    model_config = DTO_CONFIG
    Id: int = Field(gt=0)
    Name: StrictStr = Field(..., min_length=1)
    ActionType: ActionTypes
    Source: StrictStr = Field(..., min_length=1)
    SourceType: SourceTypes
    Cmd: str
    Target: StrictStr = Field(..., min_length=1)
    TargetType: TargetTypes
    Delay: int = Field(86400, ge=0)
    Retry: int = Field(3, ge=0)
    StartUp: bool = Field(False)
    RunOnce: bool = Field(True)
    RunNext: Optional[Tuple[int, ...]] = None
    LastHash: Optional[str] = None


class JobConfig(BaseModel, Generic[INPUTTYPE]):
    model_config = DTO_CONFIG
    Type: JobTypes
    Config: INPUTTYPE
    KWARGS: Dict[Any, Any] = None


class EnqueueRequest(BaseModel):
    model_config = DTO_CONFIG
    JobType: JobTypes
    Job: JobConfig
    EnqueueGate: bool
    DeferBy: Optional[Any] = None
    ReEnqueue: Optional[bool] = False
    ReEnqueueId: Optional[str] = None


class LifespanContext(BaseModel):
    model_config = DTO_EDGE_CONFIG
    Locker: Any
    AsyncSleep: Callable[[float], Awaitable[None]]
    SubProcess: Any
    EnqueueGate: bool


class WorkerInit(BaseModel):
    model_config = DTO_EDGE_CONFIG

    Broker: AsyncBroker
    Backend: AsyncResultBackend[Any]
    RedisURL: str
    RedisClient: Redis
