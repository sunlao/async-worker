from pydantic import BaseModel
from asyncpg import Connection as AsyncConnection
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.constants import UserContext, DBPoolOutcome
from shared.models.policy import DTO_EDGE_CONFIG, DTO_CONFIG
from shared.models.log import Config


class DBConnectEvent(BaseModel):
    model_config = DTO_CONFIG
    ConnectElapsed_ms: int
    DBOpenOutcome: DBPoolOutcome


class DBStartUpContext(BaseModel):
    """DTO to manage passing startup context from the edges to the DB Engine"""

    model_config = DTO_EDGE_CONFIG
    UserContext: UserContext
    Log: Writer
    LogErrorHelper: Error
    Config: Config
    DBMaxPool: int


class DBConnInput(BaseModel):
    """DTO Internal Passing of data to open a connection"""

    model_config = DTO_CONFIG
    UserContext: UserContext
    Config: Config
    StartElapsed: float


class DBConnection(BaseModel):
    """DTO Internal Passing of data and objects back to engine after
    opening a connection"""

    model_config = DTO_EDGE_CONFIG
    Connection: AsyncConnection
    Elapsed_ms: float
