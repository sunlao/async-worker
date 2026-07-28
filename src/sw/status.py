import asyncio
import os
from redis.asyncio import Redis


class Status:
    def __init__(self):
        self.redis = Redis(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            decode_responses=True,
        )

    async def _enqueued(self, broker) -> list[str]:
        groups = await self.redis.xinfo_groups(broker.queue_name)
        id = groups[0]["last-delivered-id"]
        entries = await self.redis.xrange(
            broker.queue_name,
            min=f"({id.decode()}",
            max="+",
        )
        return [
            broker.formatter.loads(fields[b"data"]).task_id for _, fields in entries
        ]

    async def _pending(self, broker) -> list[str]:
        stream = await self.redis.xpending_range(
            broker.queue_name,
            broker.consumer_group_name,
            min="-",
            max="+",
            count=1000,
        )
        tasks = await asyncio.gather(
            *[
                self.redis.xrange(
                    broker.queue_name,
                    min=item["message_id"],
                    max=item["message_id"],
                    count=1,
                )
                for item in stream
            ]
        )
        return [
            broker.formatter.loads(fields[b"data"]).task_id
            for task in tasks
            for _, fields in task
        ]

    async def _check_exist(self, broker, stream_ids: list[str], job_id: int) -> bool:
        tasks = await asyncio.gather(
            *[
                self.redis.xrange(
                    broker.queue_name, min=stream_id, max=stream_id, count=1
                )
                for stream_id in stream_ids
            ]
        )
        return any(
            message.labels.get("job_id") == job_id
            for task in tasks
            for _, fields in task
            if (message := broker.formatter.loads(fields[b"data"]))
        )

    async def job_id_in_work(self, broker, job_id: int) -> bool:
        enqueued, pending = await asyncio.gather(
            self._enqueued(broker),
            self._pending(broker),
        )
        ids = enqueued + pending
        return self._check_exist(broker, ids, job_id)
