from typing import Any
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult
from shared.models.worker import WorkerInitContext


class DuplicateJobError(RuntimeError):
    pass


class UniqueJob(TaskiqMiddleware):
    """Extend taskiq middleware to enforce unique jobs submission in support of
    idompotentcy"""

    JOB_ID = "job_id"
    KEY_PREFIX = "taskiq:job:"

    def __init__(self, context: WorkerInitContext) -> None:
        self.context = context

    def _key(self, job_id: int | str) -> str:
        return f"{self.KEY_PREFIX}{job_id}"

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        """Use Taskiq's pre_send middleware hook to atomically claim the job ID in Redis
        before enqueueing the message, rejecting the submission if the claim already
        exists."""
        job_id = message.labels[self.JOB_ID]
        claimed = await self.context.RedisClient.set(self._key(job_id), 1, nx=True)
        if not claimed:
            raise DuplicateJobError(f"Job '{job_id}' is already active.")
        return message

    async def post_save(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        """Use Taskiq's post_save middleware hook to remove the job claim after
        acknowledgement (because ack_type=when_executed)."""
        job_id = message.labels[self.JOB_ID]
        await self.context.RedisClient.delete(self._key(job_id))
