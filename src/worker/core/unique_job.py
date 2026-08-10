from typing import Any
from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult
from shared.log.helpers.core import build as core_log
from shared.models.constants import Events, LogLevel
from shared.models.log import CoreError


class DuplicateJobError(RuntimeError):
    pass


class UniqueJob(TaskiqMiddleware):
    """Enforce one queued, delayed, or executing instance per job ID."""

    JOB_ID = "job_id"
    SCHEDULE_ID = "schedule_id"
    KEY_PREFIX = "taskiq:job:"
    CLAIM_SCRIPT = """
    local current = redis.call("GET", KEYS[1])
    if not current then
        redis.call("SET", KEYS[1], ARGV[1])
        return 1
    end
    if current == ARGV[1] then
        return 1
    end
    return 0
    """
    RELEASE_SCRIPT = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    end
    return 0
    """

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    def _key(self, job_id: int | str) -> str:
        return f"{self.KEY_PREFIX}{job_id}"

    def _log_error(self, job_id: int | str, error: Exception) -> CoreError:
        context = self.broker.state
        msg = f"Post Save failed for Job Id: {job_id}"
        core = core_log(context["config_log"], LogLevel.ERROR, Events.ENQUEUE, msg)
        dto = CoreError(
            Core=core,
            Error=context["log_error_helper"].trace_back_nfo(error),
        )
        context["log"].write_core_error(dto)
        return dto

    @classmethod
    def _token(cls, message: TaskiqMessage) -> str:
        return str(message.labels.get(cls.SCHEDULE_ID, message.task_id))

    async def claim(self, job_id: int | str, token: str) -> None:
        claimed = await self.redis.eval(self.CLAIM_SCRIPT, 1, self._key(job_id), token)
        if claimed != 1:
            raise DuplicateJobError(f"Job '{job_id}' is already active.")

    async def release(self, job_id: int | str, token: str) -> None:
        await self.redis.eval(self.RELEASE_SCRIPT, 1, self._key(job_id), token)

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        job_id = message.labels[self.JOB_ID]
        await self.claim(job_id, self._token(message))
        return message

    async def post_save(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        job_id = message.labels[self.JOB_ID]
        try:
            await self.release(job_id, self._token(message))
            if result.is_err:
                return
            from worker.core.post_process import PostProcess
            await PostProcess(self.broker.state).execute(job_id)
        except Exception as error:  # pylint: disable=broad-exception-caught
            self._log_error(job_id, error)
