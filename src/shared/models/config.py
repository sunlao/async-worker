from pydantic import BaseModel
from taskiq.middlewares import SmartRetryMiddleware
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from shared.models.constants import DBUser
from shared.models.constants import Environments
from shared.models.policy import DTO_CONFIG


class DBSecrets(BaseModel):
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
    Broker: type[RedisStreamBroker]
    Backend: type[RedisAsyncResultBackend]
    Middleware: type[SmartRetryMiddleware]


class Quiesce(BaseModel):
    model_config = DTO_CONFIG
    GatePath: str
    TimeOut: int
    DBMaxPool: int
