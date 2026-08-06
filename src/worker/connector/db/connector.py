from typing import Any
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

    @staticmethod
    def _args(
        name: str, args: tuple[tuple[str, Any], ...], **kwargs
    ) -> tuple[tuple[str, Any], ...]:
        match = next((v for k, v in kwargs.items() if k == name), None)
        if match is None:
            return args
        return tuple(tuple(arg) for arg in match)

    async def _execute_db_pool(
        self, conn, action_type, sql, args
    ):
        async with self.db.client() as conn:
            if action_type == ActionTypes.SELECT_ONE:
                return await conn.fetchrow(sql, args)
            if action_type == ActionTypes.SELECT_MANY:
                return await conn.fetch(sql, args)
            if action_type == ActionTypes.EXECUTE_ONE:
                return await conn.execute(sql, args)
            if action_type == ActionTypes.EXECUTE_MANY:
                return await conn.executemany(sql, args)


    async def execute_db_pool_all(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        queries = exe.JobConfig.Queries
        for q in queries:
            args = self._args(q.Name, q.Args, **kwargs)
            print(f"q: {q}")
            print(f"kwarg: {kwargs.items()}")
            # sql = self.query.get(q.Name)
        # async with self.db.client() as conn:
        #     if exe.JobConfig.ActionType == ActionTypes.SELECT_ONE:
        #         return await conn.fetchrow(sql)
