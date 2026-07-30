from typing import Any
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult
from shared.models.worker import EnqueueRequest, WorkerInit


class DuplicateJobError(RuntimeError):
    pass


class UniqueJob(TaskiqMiddleware):
    _JOB_ID = "job_id"
    _KEY_PREFIX = "taskiq:job:"

    def __init__(self, worker: WorkerInit) -> None:
        self.worker = worker

    def _key(self, job_id: int | str) -> str:
        return f"{self._KEY_PREFIX}{job_id}"

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        job_id = message.labels[self._JOB_ID]
        claimed = await self.worker.RedisClient.set(self._key(job_id), 1, nx=True)
        if not claimed:
            raise DuplicateJobError(f"Job '{job_id}' is already active.")
        return message

    async def post_save(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        job_id = message.labels[self._JOB_ID]
        await self.worker.RedisClient.delete(self._key(job_id))
