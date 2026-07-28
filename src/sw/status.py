import asyncio
import os
from redis.asyncio import Redis
from taskiq.message import TaskiqMessage


class Status:
    def __init__(self):
        self.redis = Redis(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            decode_responses=False,
        )

    async def _enqueued(self, broker) -> list[TaskiqMessage]:
        groups = await self.redis.xinfo_groups(broker.queue_name)
        last_delivered_id = groups[0]["last-delivered-id"]
        entries = await self.redis.xrange(
            broker.queue_name, min=f"({last_delivered_id.decode()}", max="+"
        )
        return [
            broker.formatter.loads(fields[b"data"])
            for _, fields in entries
        ]

    async def _pending(self, broker) -> list:
        pending = await self.redis.xpending_range(
            broker.queue_name,
            broker.consumer_group_name,
            min="-",
            max="+",
            count=1000,
        )
        entries = await asyncio.gather(
            *[
                self.redis.xrange(
                    broker.queue_name,
                    min=item["message_id"],
                    max=item["message_id"],
                    count=1,
                )
                for item in pending
            ]
        )
        return [
            broker.formatter.loads(fields[b"data"])
            for entry in entries
            for _, fields in entry
        ]

    async def _check_exist(self, messages: list[TaskiqMessage], job_id: int) -> bool:
        return any(message.labels.get("job_id") == job_id for message in messages)

    async def job_id_in_work(self, broker, job_id: int) -> bool:
        enqueued, pending = await asyncio.gather(
            self._enqueued(broker), self._pending(broker)
        )
        return await self._check_exist(enqueued + pending, job_id)
