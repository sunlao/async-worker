from datetime import datetime
from typing import Any, Awaitable, Callable, Generic, Optional
from redis.asyncio import Redis
from taskiq import AsyncBroker
from taskiq.abc.result_backend import AsyncResultBackend
from pydantic import BaseModel, Field, StrictStr, UUID4
from shared.models.constants import ActionTypes, JobTypes, Targets, ConnectionProfileTypes
from shared.models.log import Config, TraceBackEvent
from shared.models.policy import DTO_CONFIG, DTO_EDGE_CONFIG, INPUTTYPE


class AdminConfig(BaseModel):
    model_config = DTO_CONFIG
    Name: StrictStr = Field(..., min_length=1)
    SourceConnectionProfile: str
    SourceActionType: ActionTypes = Field(default=ActionTypes.SELECT_MANY)
    SourceCmd: str = Field("")
    TargetConnectionProfile: str
    TargetActionType: ActionTypes = Field(default=ActionTypes.EXECUTE_MANY)
    TargetCmd: str = Field("")
    StartUp: bool = Field(default=True)
    Delay: int = Field(default=600, ge=0)
    RunOnce: bool = Field(default=False)
    RunNext: Optional[tuple[int, ...]] = None
    Retry: int = Field(default=3, ge=0)


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
    ActionType: ActionTypes = Field(ActionTypes.POST)
    Message: str
    Status: bool
    AdminResults: Optional[AdminJobResult] = None
    Start: datetime
    End: datetime
    DurationMs: int = Field(ge=0)


class ConnectionProfile(BaseModel, Generic[INPUTTYPE]):
    model_config = DTO_EDGE_CONFIG
    Name: str
    Type: ConnectionProfileTypes
    PlatformResource: Any | None = None
    Config: INPUTTYPE | None = None


class EnqueueResponse(BaseModel):
    model_config = DTO_EDGE_CONFIG
    JobId: int
    DelayId: str | None = None
    RunId: str | None = None


class ExecutionConfig(BaseModel, Generic[INPUTTYPE]):
    model_config = DTO_CONFIG
    JobId: int = Field(gt=0)
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


class HelloConfig(BaseModel):
    model_config = DTO_CONFIG
    Name: StrictStr = Field(..., min_length=1)
    ConnectionProfile: str
    ActionType: ActionTypes
    Cmd: str
    StartUp: bool = Field(default=False)
    Delay: int = Field(default=0, ge=0)
    RunOnce: bool = Field(default=True)
    RunNext: Optional[tuple[int, ...]] = None
    Retry: int = Field(default=3, ge=0)


class HelloJobResult(BaseModel):
    model_config = DTO_CONFIG
    RowCount: int
    ActionType: ActionTypes
    LastHash: Optional[str] = None


class HelloEvent(BaseModel):
    model_config = DTO_CONFIG
    JobId: int = Field(gt=0)
    JobName: str
    Target: Targets
    Status: bool
    Message: str
    Start: datetime
    End: datetime
    DurationMs: int = Field(ge=0)
    Result: Optional[HelloJobResult] = None


class JobConfig(BaseModel, Generic[INPUTTYPE]):
    model_config = DTO_CONFIG
    Type: JobTypes
    Id: int = Field(gt=0)
    KWARGS: tuple[tuple[Any, Any], ...] = ()
    Config: INPUTTYPE


class LifespanContext(BaseModel):
    model_config = DTO_EDGE_CONFIG
    Locker: Any
    Queue: AsyncBroker
    AsyncSleep: Callable[[float], Awaitable[None]]
    Gather: Callable[..., Awaitable[list[Any]]]
    SubProcess: Any
    EnqueueGate: bool


class LogCoreInput(BaseModel):
    model_config = DTO_CONFIG
    ConfigLog: Config
    TransactionID: UUID4
    Name: str


class WorkerConfig(BaseModel):
    model_config = DTO_CONFIG
    StartUp: bool
    JobPath: str
    JobVersion: str
    DBMaxPool: int
    DataDir: str
    GatePath: str


class WorkerInitContext(BaseModel):
    model_config = DTO_EDGE_CONFIG
    Broker: AsyncBroker
    Backend: AsyncResultBackend[Any]
    RedisURL: str
    RedisClient: Redis
