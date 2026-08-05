from shared.db.helpers.query import Query
from shared.models.constants import ActionTypes
from shared.models.worker import (
    ExecutionConfig,
    HelloConfig,
    ConnectionProfile,
)


class DBConnectorError(RuntimeError):
    """Raised when the DB connector cannot produce valid rows."""


class Connector:
    """CLI connector to interface"""

    def __init__(self):
        self.query = Query()

    async def execute_db_pool(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, conn, **kwargs
    ):
        print(f"action type: {exe.JobConfig.ActionType}")
        if exe.JobConfig.ActionType == ActionTypes.SELECT_ONE:
            row = await conn.fetchrow(self.query.get(exe.JobConfig.Cmd))
            print(f"row: {row}")
            pass
        pass
