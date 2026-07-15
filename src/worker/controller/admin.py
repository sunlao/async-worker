# pylint: disable=duplicate-code
from datetime import UTC
from worker.enqueuer.route import Route
from shared.helper.ops_ledger import OpsLedger
from shared.models.constants import JobTypes
from shared.models.worker import (
    AdminEvent,
    ExecutionConfig,
    AdminConfig,
    AdminJobResult,
    JobConfig,
)


class Admin:
    """Admin Controller: Executes jobs transform raw data into the curated"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.config_log = self.ctx["config_log"]
        self.time_counter = self.config_log.TimeCounter
        ops_ledger = OpsLedger(ctx["arq_client"], ctx["db"], self.config_log.UUID4)
        self.methods = {"OpsLedger": ops_ledger.load}

    def _event(
        self, config_exe: ExecutionConfig, msg: str, results: AdminJobResult | None
    ) -> AdminEvent:
        config_job = config_exe.JobConfig
        return AdminEvent(
            JobId=config_job.Id,
            JobName=config_job.Name,
            Message=msg,
            Status=True,
            AdminResults=results,
            Start=config_exe.Start,
            End=self.config_log.Now(UTC),
            DurationMs=int((self.time_counter() - config_exe.StartCounter) * 1000),
        )

    async def _enqueue(
        self,
        config_exe: ExecutionConfig,
        msg: str,
        result: AdminJobResult = None,
        **kwargs,
    ) -> AdminEvent:
        config_job = config_exe.JobConfig
        enqueue_dto = JobConfig(Type=JobTypes.ADMIN, Config=config_job, KWARGS=kwargs)
        enqueue = await Route(self.ctx).execute(True, JobTypes.ADMIN, enqueue_dto)
        e_msg = f"{msg}" f" - {enqueue.Message} with status {enqueue.Status}"
        return self._event(config_exe, e_msg, result)

    async def _results(self, config: AdminConfig) -> AdminJobResult:
        start = self.time_counter()
        method = self.methods[config.Name]
        results = await method()
        return AdminJobResult(
            ExecutionId=results.ExecutionId,
            Status=True,
            Code=results.Code,
            Message=results.Message,
            DurationMs=int((self.time_counter() - start) * 1000),
        )

    async def execute(self, config_exe: ExecutionConfig, **kwargs) -> AdminEvent:
        """Controler to execute Admin jobs"""
        try:
            results = await self._results(config_exe.JobConfig)
            msg = "admin completed"
            return await self._enqueue(config_exe, msg, results, **kwargs)
        except Exception as e:
            raise e
