from pydantic import BaseModel, ConfigDict, NonNegativeInt
from taskiq import TaskiqState


class Reporter:
    def __init__(self, context: TaskiqState):
        self.redis = context.RedisClient
        self.stream = context.QueueName
        self.group = context.ConsumerGroup

    async def state(self) -> ReportState:
        redis_healthy = await self.redis.ping()
        groups = await self.redis.xinfo_groups(self.stream)
        group = next(
            item
            for item in groups
            if self._text(item["name"]) == self.group
        )
        in_flight = group["pending"]
        return ReportState(
            Enqueued=group["lag"],
            InFlight=in_flight,
            Acknowledged=group["entries-read"] - in_flight,
            RedisHealthy=redis_healthy,
        )

    @staticmethod
    def _text(value: str | bytes) -> str:
        return value.decode() if isinstance(value, bytes) else value