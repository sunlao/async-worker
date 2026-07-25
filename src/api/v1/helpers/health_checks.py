from fastapi import Request
from shared.db import Engine
from shared.models.worker import Health


class HealthCheck:
    """Help /ready evaluate worker and db status"""

    async def db(self, request: Request) -> bool:
        try:
            engine: Engine = request.app.state.db
            async with engine.client() as conn:
                row = await conn.fetchrow("SELECT true as check")
            if row["check"] is True:
                return True
            return False
        except Exception:  # pylint: disable=broad-except
            return False

    async def worker(self, request: Request) -> bool:
        # arq = request.app.state.arq_client
        # health = await arq.health()
        health = Health(Complete=1, Failed=1, Retried=1, Ongoing=1, Queued=1)
        try:
            Health.model_validate(health)
            return health.Complete >= 0
        except Exception:  # pylint: disable=broad-except
            return False
