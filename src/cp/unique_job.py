from typing import Any
from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult


class DuplicateJobError(RuntimeError):
    """Raised when a job is already queued or executing."""


class UniqueJob(TaskiqMiddleware):
    _JOB_ID = "job_id"
    _KEY_PREFIX = "taskiq:job:"
    _RELEASE_SCRIPT = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    end
    return 0
    """

    def __init__(self, redis: Redis, *, timeout_seconds: int = 86_400) -> None:
        self._redis = redis
        self._timeout_seconds = timeout_seconds

    def _job_id(self, message: TaskiqMessage) -> str:
        job_id = message.labels.get(self._JOB_ID)
        if not job_id:
            raise ValueError("Taskiq message requires a non-empty 'job_id' label.")
        return str(job_id)

    def _key(self, job_id: str) -> str:
        return f"{self._KEY_PREFIX}{job_id}"

    async def _release(self, message: TaskiqMessage) -> None:
        await self._redis.eval(
            self._RELEASE_SCRIPT, 1, self._key(self._job_id(message)), message.task_id
        )

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        job_id = self._job_id(message)
        key = self._key(job_id)
        current_run_id = await self._redis.get(key)
        if current_run_id == message.task_id:
            return message
        acquired = await self._redis.set(
            key, message.task_id, nx=True, ex=self._timeout_seconds
        )
        if not acquired:
            raise DuplicateJobError(f"Job '{job_id}' is already queued or executing.")
        return message

    async def post_save(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        if result.error is not None:
            return
        await self._release(message)
