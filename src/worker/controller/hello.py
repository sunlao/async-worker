from datetime import UTC
from worker.connector.io.connector import Connector as CLI
from worker.connector.api.connector import Connector as API
from shared.models.constants import JobTypes, ActionTypes, Targets
from shared.models.worker import (
    HelloEvent,
    ExecutionConfig,
    HelloConfig,
    JobConfig,
    HelloJobResult,
)


class HelloErrorHandling(Exception):
    def __init__(self, p_job_id):
        super().__init__(
            f"{p_job_id} failed as part of Hello Controller error handling"
        )


class Hello:
    """Hello Controller demonstrates worker functionality"""

    def __init__(self, ctx, conn):
        self.ctx = ctx
        self.conn = conn
        self.log = self.ctx["config_log"]
        self.gate = ctx["enqueue_gate"]

    async def _api_actions(self, exe: ExecutionConfig[HelloConfig], **kwargs):
        pass

    async def _db_actions(self, exe: ExecutionConfig[HelloConfig], **kwargs):
        pass

    async def _io_actions(self, exe: ExecutionConfig[HelloConfig], **kwargs):
        pass

    async def _enqueue(
        self,
        config_exe: ExecutionConfig[HelloConfig],
        msg: str,
        result: HelloJobResult,
        **kwargs,
    ) -> HelloEvent:
        config_job = config_exe.JobConfig
        dto = JobConfig(Type=JobTypes.MOVEMENT, Config=config_job, KWARGS=kwargs)
        enqueue = await Route(self.ctx).execute(True, JobTypes.MOVEMENT, dto, result)
        e_msg = f"{msg}" f" - {enqueue.Message} with status {enqueue.Status}"
        return self._event(config_exe, e_msg, result)

    def _event(
        self, exe: ExecutionConfig[HelloConfig], msg: str, result: HelloJobResult
    ) -> HelloEvent:
        return HelloEvent(
            JobId=exe.JobId,
            JobName=exe.JobConfig.Name,
            Target=exe.JobConfig.Target,
            Status=True,
            Message=msg,
            Start=exe.Start,
            End=self.log.Now(UTC),
            DurationMs=int((self.log.TimeCounter() - exe.StartCounter) * 1000),
            Result=result,
        )

    async def execute(self, exe: ExecutionConfig[HelloConfig], **kwargs) -> HelloEvent:
        """Controller to execute Hello jobs Action Types by controller"""
        action_type = exe.JobConfig.ActionType
        if action_type in (
            ActionTypes.SELECT_ONE,
            ActionTypes.SELECT_MANY,
            ActionTypes.EXECUTE_MANY,
            ActionTypes.EXECUTE_ONE,
        ):
            self._db_actions(exe, **kwargs)
        if action_type in (ActionTypes.ECHO):
            self._io_actions(exe, **kwargs)
        if action_type in (ActionTypes.GET, ActionTypes.POST):
            self._api_actions(exe, **kwargs)
        msg = "Movement Controller: Completed run"
        return await self._enqueue(config_exe, msg, trg_result, **kwargs)
