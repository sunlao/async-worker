from typing import Any
from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult
from shared.log.helpers.core import build as core_log
from shared.models.constants import EnqueueTypes, Events, LogLevel
from shared.models.log import CoreError
from shared.models.worker import EnqueueResponse
from worker.client import Client
from worker.core.extensions.lua import release_script


class Acknowledge(TaskiqMiddleware):
    """Use frameworkd middleware to extend capabilities when performing an acknowledge action
    - Ensure only one unqique job id can be enqueued or submitted for a delayed enqueue
    - post_save is a reserved word for actions taken after acknowledge action when the framework
    is started with ack-type when_executed
    """

    JOB_ID = "job_id"
    SCHEDULE_ID = "schedule_id"
    KEY_PREFIX = "taskiq:job:"

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def _enqueue(
        self, client: Client, job_id: int, type: EnqueueTypes
    ) -> EnqueueResponse:
        job = self.broker.state.job.config(job_id)
        return await client.enqueue(job, type)

    def _key(self, job_id: int | str) -> str:
        return f"{self.KEY_PREFIX}{job_id}"

    def _log_error(self, job_id: int | str, error: Exception) -> CoreError:
        context = self.broker.state
        msg = f"Acknowledge post processing failed for Job Id: {job_id}"
        core = core_log(context["config_log"], LogLevel.ERROR, Events.ACKNOWLEDGE, msg)
        dto = CoreError(
            Core=core,
            Error=context["log_error_helper"].trace_back_nfo(error),
        )
        context["log"].write_core_error(dto)
        return dto

    async def _post_process(self, job_id):
        context = self.broker.state
        job = context.job.config(job_id)
        client = Client(context)
        processes = []
        if job.Config.RunOnce is False:
            processes.append((job.Id, EnqueueTypes.REENQUEUE))
        for i in job.Config.RunNext:
            processes.append((i, EnqueueTypes.NEXT))
        if len(processes) == 0:
            return
        await context.gather(
            *(self._enqueue(client, id, type) for id, type in processes)
        )

    async def _release(self, job_id: int | str, token: str) -> None:
        await self.redis.eval((release_script()), 1, self._key(job_id), token)

    @classmethod
    def _token(cls, message: TaskiqMessage) -> str:
        return str(message.labels.get(cls.SCHEDULE_ID, message.task_id))

    async def post_save(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        job_id = int(message.labels[self.JOB_ID])
        try:
            await self._release(job_id, self._token(message))
            if result.is_err:
                return
            await self._post_process(job_id)
        except Exception as error:  # pylint: disable=broad-exception-caught
            self._log_error(job_id, error)
