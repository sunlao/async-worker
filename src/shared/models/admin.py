from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, StrictStr, UUID4
from shared.models.constants import (
    ActionTypes,
    JobTypes,
    SourceTypes,
    TargetTypes,
)
from shared.models.config import Quiesce
from shared.models.policy import DTO_CONFIG, DTO_EDGE_CONFIG


class LedgerData(BaseModel):
    model_config = {**DTO_CONFIG, "populate_by_name": True}
    JobType: JobTypes = Field(alias="job_type")
    JobId: int = Field(gt=0, alias="job_id")
    Name: StrictStr = Field(..., min_length=1, alias="job_name")
    ActionType: ActionTypes = Field(alias="action_type")
    Source: Optional[str] = Field(alias="source")
    SourceType: Optional[SourceTypes] = Field(alias="source_type")
    Target: Optional[str] = Field(alias="job_target")
    TargetType: Optional[TargetTypes] = Field(alias="target_type")
    Cmd: str = Field(alias="cmd")
    StartUp: bool = Field(False, alias="startup")
    RunOnce: bool = Field(True, alias="run_once")
    RunNext: str = Field(default=None, alias="run_next")
    JobTry: int = Field(True, alias="job_try")
    RunId: str = Field(True, alias="run_id")
    EnqueueTime: datetime = Field(True, alias="enqueue_time")
    StartTime: datetime = Field(True, alias="start_time")
    FinishTime: datetime = Field(True, alias="finish_time")
    Status: bool = Field(True, alias="job_status")
    Message: str = Field(True, alias="job_message")


class AdminExecutionResults(BaseModel):
    model_config = DTO_CONFIG
    ExecutionId: UUID4
    Code: int
    Message: str
    Error: Optional[str] = None


class QuiesceQueue(BaseModel):
    model_config = DTO_EDGE_CONFIG
    Arq: Any
    Config: Quiesce
    Sleep: Any
    Monotonic: Any
    UUID: Any
