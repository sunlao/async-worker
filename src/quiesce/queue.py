from shared.models.api import AdminExecutionResults, QuiesceQueue


class Queue:
    def __init__(self, params: QuiesceQueue):
        self.config = params.Config
        self.arq = params.Arq
        self.sleep = params.Sleep
        self.monotonic = params.Monotonic
        self.uuid = params.UUID

    async def delete(self):
        await self.arq.delete()
        msg = "Delete all keys from all queues"
        return AdminExecutionResults(ExecutionId=self.uuid(), Code=0, Message=msg)

    async def drain(self) -> bool:
        start = self.monotonic()
        while self.monotonic() - start < self.config.TimeOut:
            health = await self.arq.health()
            if health.Ongoing <= 0:
                return AdminExecutionResults(
                    ExecutionId=self.uuid(), Code=0, Message="Drain Complete"
                )
            await self.sleep(5)
        raise RuntimeError("Could not drain in time")
