from typing import Any

from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult
from taskiq.exceptions import NoResultError


class DuplicateJobError(RuntimeError):
    pass


class UniqueJob(TaskiqMiddleware):
    _JOB_ID = "job_id"
    _KEY_PREFIX = "taskiq:job:"

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, job_id: int | str) -> str:
        return f"{self._KEY_PREFIX}{job_id}"

    async def exists(self, job_id: int | str) -> bool:
        return bool(await self._redis.exists(self._key(job_id)))

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        job_id = message.labels[self._JOB_ID]
        claimed = await self._redis.set(self._key(job_id), 1, nx=True)
        if not claimed:
            raise DuplicateJobError(f"Job '{job_id}' is already active.")
        return message

    async def post_save(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        if isinstance(result.error, NoResultError):
            return
        job_id = message.labels[self._JOB_ID]
        await self._redis.delete(self._key(job_id))