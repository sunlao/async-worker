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
    """DB connector for all controllers"""

    def __init__(self, context):
        self.db = context["db"]
        self.query = Query()

    async def execute_db_pool(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        queries = exe.JobConfig.Queries
        print(f"queries: {queries}")
        for q in queries:
            print(f"q: {q}")
        
        # sql = self.query.get(exe.JobConfig.Cmd)
        # async with self.db.client() as conn:
        #     if exe.JobConfig.ActionType == ActionTypes.SELECT_ONE:
        #         return await conn.fetchrow(sql)
