from fastapi import Request
from shared.db import Engine


class Health:
    """Help /ready evaluate worker and db status"""

    def __init__(self, request: Request):
        self.engine: Engine = request.app.state.db
        self.worker_client = request.app.state.worker

    async def db(self) -> bool:
        try:
            async with self.engine.client() as conn:
                row = await conn.fetchrow("SELECT true as check")
            if row["check"] is True:
                return True
            return False
        except Exception:  # pylint: disable=broad-except
            return False

    async def redis(self) -> bool:
        return await self.worker_client.redis_ping()

    async def worker(self) -> bool:
        return await self.worker_client.health()
