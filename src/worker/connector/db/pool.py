from typing import Any
from shared.db.helpers.query import Query
from shared.models.constants import ActionTypes
from shared.models.worker import ConnecterDBPoolInput


class PoolError(RuntimeError):
    """Raised when the DB connector cannot produce valid rows."""


class Pool:
    """Connector for Platform owned db client that passes a db pool resource from the
    edge
    - Execute SQL by action type
        - Select one
        - Select many
        - Execute one
        - Excute many
    - Use SQL helper to paas in sql by name
    - Controller may overide job config args with KWARGS
    """

    def __init__(self, context):
        self.db = context["db"]
        self.query = Query()

    @staticmethod
    def _args(
        args: tuple[Any, ...] = (),
        **kwargs: Any,
    ) -> tuple[Any, ...]:
        return tuple(kwargs.get("args_orveride", args))

    async def execute(self, input: ConnecterDBPoolInput, **kwargs):
        args = self._args(input.Args, **kwargs)
        async with self.db.client() as conn:
            if input.ActionType == ActionTypes.SELECT_ONE:
                if args == ():
                    return await conn.fetchrow(self.query.get(input.SQLName))
                return await conn.fetchrow(self.query.get(input.SQLName), *args)
            if input.ActionType == ActionTypes.SELECT_MANY:
                if args == ():
                    return await conn.fetch(self.query.get(input.SQLName))
                return await conn.fetch(self.query.get(input.SQLName), *args)
            if input.ActionType == ActionTypes.EXECUTE_ONE:
                if args == ():
                    return await conn.execute(self.query.get(input.SQLName))
                return await conn.execute(self.query.get(input.SQLName), *args)
            if input.ActionType == ActionTypes.EXECUTE_MANY:
                if args == ():
                    return await conn.executemany(self.query.get(input.SQLName))
            return await conn.executemany(self.query.get(input.SQLName), (args,))
