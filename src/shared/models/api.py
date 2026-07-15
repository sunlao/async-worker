from uuid import UUID
from datetime import datetime
from typing import Optional, Any, Mapping, Tuple
from http import HTTPMethod, HTTPStatus
from pydantic import BaseModel, Field
from fastapi import Request, Response
from shared.models.constants import ArqStatus, ProfileAction
from shared.models.policy import DTO_CONFIG, DTO_EDGE_CONFIG


class aworkConfig(BaseModel):
    model_config = DTO_CONFIG
    JobPath: str
    JobVersion: str
    AppVersion: str
    DBMaxPool: int
    GatePath: str


class Countries(BaseModel):
    model_config = DTO_CONFIG
    Countries: Tuple[str, ...]
    Count: int


class StatesRequest(BaseModel):
    model_config = DTO_CONFIG
    Country: str


class States(BaseModel):
    model_config = DTO_CONFIG
    States: Tuple[Tuple[str, str], ...]
    Count: int


class CountiesRequest(BaseModel):
    model_config = DTO_CONFIG
    Country: str
    State: str


class Counties(BaseModel):
    model_config = DTO_CONFIG
    Counties: Tuple[Tuple[str, str, str], ...]
    Count: int


class ProfileRequest(BaseModel):
    model_config = DTO_CONFIG
    LocationId: UUID
    Name: str
    BirthDateTime: datetime


class Profile(BaseModel):
    model_config = DTO_CONFIG
    ProfileId: UUID
    Action: ProfileAction


class Cities(BaseModel):
    model_config = DTO_CONFIG
    Cities: Tuple[Tuple[str, str, str, str], ...]
    Count: int


class CitiesRequest(BaseModel):
    model_config = DTO_CONFIG
    Country: str
    State: str
    County: str


class LocationRequest(BaseModel):
    model_config = DTO_CONFIG
    Country: str
    State: str
    County: str
    City: str


class Location(BaseModel):
    model_config = DTO_CONFIG
    LocationId: UUID


class APIEvent(BaseModel):
    """DTO - For API Event Log Output"""

    model_config = DTO_CONFIG
    Method: HTTPMethod
    RoutePathTemplate: str
    RouteName: str
    RequestPath: str
    PathParams: Mapping[str, str]
    Status: HTTPStatus
    DurationMs: int = Field(ge=0)
    RequestSize: int = Field(ge=0, le=2_097_152)
    ResponseSize: int = Field(ge=0, le=10_485_760)


# Support dynamic ASGI DTOs. ASGI objects are "frozen" at the edge as logging events
class ASGIEvent(BaseModel):
    """DTO - for API Log Event Input"""

    model_config = DTO_EDGE_CONFIG
    Request: Request
    Response: Response
    DurationMS: int = Field(ge=0)


class InfoResponse(BaseModel):
    """DTO for api output /info"""

    model_config = DTO_CONFIG
    FastApiVersion: str
    aworkVersion: str


# @dto(schema_extra=lambda cls: {"Title": "Immutable DTO for the /ready"})
class ReadyResponse(BaseModel):
    """DTO for api output /ready"""

    model_config = DTO_CONFIG
    DBCheck: bool
    WorkerCheck: bool


class EnqueueResponse(BaseModel):
    """DTO for api output /enqueue"""

    model_config = DTO_CONFIG
    RunID: str  # Use str becausae we return n/a when already enequeued
    Message: str
    Status: str


class RunResponse(BaseModel):
    """DTO for api output /Runs by id and used internally by DTO Runs"""

    model_config = DTO_CONFIG
    RunID: str
    Status: ArqStatus
    Info: Optional[Any]
    Error: Optional[Any]


class Runs(BaseModel):
    """Internal DTO for passing a list of jobs"""

    model_config = DTO_CONFIG
    Runs: tuple[RunResponse, ...]


class RunsResponse(BaseModel):
    """DTO for api output /jobs to list all Jobs"""

    model_config = DTO_CONFIG
    Runs: tuple[RunResponse, ...]
    Errors: int


class JobStatusAllResponse(BaseModel):
    """DTO for api output /jobs for all jobs"""

    model_config = DTO_CONFIG
    Count: int
    Results: Any


class RootResponse(BaseModel):
    """DTO for api output /"""

    model_config = DTO_CONFIG
    Message: str


class Routes(BaseModel):
    """Internal DTO for for helper.log"""

    model_config = DTO_CONFIG
    RoutePathTemplate: str
    RouteName: str
    RequestPath: str


class TargetAuditDetailResponse(BaseModel):
    """DTO - For API Event Log Output"""

    model_config = DTO_CONFIG
    Hash: Optional[str] = None
