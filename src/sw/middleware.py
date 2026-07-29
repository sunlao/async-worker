from typing import Any
from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult


class ActiveJobMiddleware(TaskiqMiddleware):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        job_id = message.labels.get("job_id")
        if job_id is not None:
            await self.redis.set(f"taskiq:active:{job_id}", message.task_id)
        return message

    async def post_execute(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        job_id = message.labels.get("job_id")
        if job_id is not None:
            await self.redis.delete(f"taskiq:active:{job_id}")
