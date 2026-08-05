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

    def __init__(self, context):
        self.db = context["db"]
        self.query = Query()

    async def execute_db_pool(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        async with self.db.client() as conn:
            sql = self.query.get(exe.JobConfig.Cmd)
            if exe.JobConfig.ActionType == ActionTypes.SELECT_ONE:
                row = await conn.fetchrow(sql)
                print(f"row: {row}")
        print(f"action type: {exe.JobConfig.ActionType}")
        pass
