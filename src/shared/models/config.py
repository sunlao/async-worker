from pydantic import BaseModel, Field
from shared.models.constants import DBPlatforms, AckTypes, AuthTypes
from shared.models.constants import Environments
from shared.models.policy import DTO_CONFIG


class ConnectionInputConfig(BaseModel):
    model_config = DTO_CONFIG
    ConnectionPath: str
    ConnectionVersion: str


class IOConfig(BaseModel):
    """DTO for IO Config"""

    model_config = DTO_CONFIG
    HOST: str
    PORT: str


class APIConfig(BaseModel):
    """DTO for API Config"""

    model_config = DTO_CONFIG
    HOST: str
    PORT: int


class DBConfig(BaseModel):
    """DTO for DB Config
    - can be used by the service or as config for ConnectionProfile
    """

    model_config = DTO_CONFIG
    PLATFORM: DBPlatforms = Field(default=DBPlatforms.POSTGRES)
    SERVICE: str | None = None
    HOST: str
    USER: str | None = None
    DB_NAME: str | None = None
    PORT: int
    AUTHTYPE: AuthTypes = Field(default=AuthTypes.PASSWORD)
    PASSWORD: str | None = None
    TOKEN: str | None = None
    SSL: bool | None = None


class JobInputConfig(BaseModel):
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
