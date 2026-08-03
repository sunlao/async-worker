from pydantic import BaseModel
from shared.models.constants import DBUser, AckTypes
from shared.models.constants import Environments
from shared.models.policy import DTO_CONFIG


class IOConfig(BaseModel):
    """DTO for Secret Config"""

    model_config = DTO_CONFIG
    HOST: str
    PORT: str


class APIConfig(BaseModel):
    """DTO for Secret Config"""

    model_config = DTO_CONFIG
    HOST: str
    PORT: int


class DBConfig(BaseModel):
    """DTO for Secret Config"""

    model_config = DTO_CONFIG
    HOST: str
    USER: DBUser
    PASSWORD: str
    DB_NAME: str
    PORT: int
    SERVICE: str


class ReaderConfig(BaseModel):
    model_config = DTO_CONFIG
    JobPath: str
    JobVersion: str


class Redis(BaseModel):
    """DTO for Redis Config"""

    model_config = DTO_CONFIG
    Host: str
    Port: int
    RedisPingAttempts: int
    RedisPingDelaySec: float
    Environment: Environments
    AppCode: str
    WaitFor: int
    ResultExpirationSec: int
    AckType: AckTypes
