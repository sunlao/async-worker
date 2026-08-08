from taskiq import TaskiqState
from shared.models.worker import ReportState


class Reporter:
    def __init__(self, context: TaskiqState):
        self.redis = context.redis_client
        self.stream = context.queue.queue_name
        self.group = context.queue.consumer_group_name

    async def state(self) -> ReportState:
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
        )

    @staticmethod
    def _text(value: str | bytes) -> str:
        return value.decode() if isinstance(value, bytes) else value