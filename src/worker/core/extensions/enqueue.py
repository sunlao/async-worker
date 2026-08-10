from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware
from worker.core.extensions.lua import release_script, claim_script

class DuplicateJobError(RuntimeError):
    pass


class Enqueue(TaskiqMiddleware):
    """Use frameworkd middleware to extend capabilities when performing an enqueue action
    - Ensure only one unqique job id can be enqueued or submitted for a delayed enqueue
    - pre_send is a reserved word for before enqueue hook (not scheduled)
    """

    JOB_ID = "job_id"
    SCHEDULE_ID = "schedule_id"
    KEY_PREFIX = "taskiq:job:"

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    def _key(self, job_id: int | str) -> str:
        return f"{self.KEY_PREFIX}{job_id}"

    @classmethod
    def _token(cls, message: TaskiqMessage) -> str:
        return str(message.labels.get(cls.SCHEDULE_ID, message.task_id))

    async def claim(self, job_id: int | str, token: str) -> None:
        """Execute LUA claim Script to 
            - Checks the Redis uniqueness key derived from job_id.
            - Sets it to the execution/schedule token if absent.
            - Accepts the same token idempotently.
            - Rejects a different token        
        - Note:
            - Worker must manually call claim before submitting a job for delay
              - no middleware support for delayed jobs (scheduled)
        """
        claimed = await self.redis.eval(claim_script(), 1, self._key(job_id), token)
        if claimed != 1:
            raise DuplicateJobError(f"Job '{job_id}' is already active.")

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        """Midleware hook for pre-enqueue actions
            - framework calls directly before enqueue
            - Worker must manually call claim before submitting a delayed job
        """
        await self.claim(message.labels[self.JOB_ID], self._token(message))
        return message

    async def release_on_error(self, job_id: int | str, token: str) -> None:
        await self.redis.eval(release_script(), 1, self._key(job_id), token)
