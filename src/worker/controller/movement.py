from datetime import UTC
from worker.connector.cli.connector import Connector as CLI
from worker.connector.api.connector import Connector as API
from worker.connector.db.postgres import Postgres
from worker.enqueuer.route import Route
from shared.models.constants import JobTypes, ActionTypes, SourceTypes, TargetTypes
from shared.models.worker import (
    MovementEvent,
    ExecutionConfig,
    MovementConfig,
    SerializeOutput,
    JobConfig,
    MovementJobResult,
    BinaryOutput,
)


class MovementErrorHandling(Exception):
    def __init__(self, p_job_id):
        super().__init__(
            f"{p_job_id} failed as part of Movement Controller error handling"
        )


class Movement:
    """Movement Controller to Get a avro DTO from a single Source and move it to a
    Singler Target by Job Type"""

    def __init__(self, ctx, conn):
        self.ctx = ctx
        self.conn = conn
        self.config_log = self.ctx["config_log"]
        self.gate = ctx["enqueue_gate"]

    async def _avro_to_trg(
        self, config_job: MovementConfig, avo_dto: SerializeOutput
    ) -> MovementJobResult:
        if config_job.TargetType == TargetTypes.PG:
            return await Postgres(self.ctx, self.conn).target(config_job, avo_dto)

    async def _binary_to_trg(
        self, config_job: MovementConfig, output: BinaryOutput
    ) -> MovementJobResult:
        if config_job.ActionType == ActionTypes.BINC:
            CLI(self.ctx).unzip(config_job.Target)
        return MovementJobResult(
            RowCount=0,
            ActionType=config_job.ActionType,
            LastHash=output.BytesSHA256,
        )

    async def _enqueue(
        self, config_exe: ExecutionConfig, msg: str, result: MovementJobResult, **kwargs
    ) -> MovementEvent:
        config_job = config_exe.JobConfig
        dto = JobConfig(Type=JobTypes.MOVEMENT, Config=config_job, KWARGS=kwargs)
        enqueue = await Route(self.ctx).execute(True, JobTypes.MOVEMENT, dto, result)
        e_msg = f"{msg}" f" - {enqueue.Message} with status {enqueue.Status}"
        return self._event(config_exe, e_msg, result)

    def _event(
        self, config_exe: ExecutionConfig, msg: str, result: MovementJobResult
    ) -> MovementEvent:
        config_job = config_exe.JobConfig
        return MovementEvent(
            JobId=config_job.Id,
            JobName=config_job.Name,
            Status=True,
            Message=msg,
            Start=config_exe.Start,
            End=self.config_log.Now(UTC),
            DurationMs=int(
                (self.config_log.TimeCounter() - config_exe.StartCounter) * 1000
            ),
            Source=config_job.Source,
            Result=result,
        )

    async def _src_to_avro(
        self, config_job: MovementConfig, **kwargs
    ) -> SerializeOutput:
        if config_job.SourceType in SourceTypes.CLI:
            return await CLI(self.ctx).source_data(config_job, **kwargs)

    async def _src_to_binary(self, config_job: MovementConfig) -> BinaryOutput:
        if config_job.SourceType == SourceTypes.API:
            return await API(self.ctx).download(
                config_job.Cmd, config_job.Source, config_job.ActionType
            )

    async def _src_is_same(self, config_exe: ExecutionConfig, **kwargs):
        """Re-enqueue jobs with no further action when source is same"""
        config_job = config_exe.JobConfig
        trg_result = MovementJobResult(
            RowCount=0,
            ActionType=config_job.ActionType,
            LastHash=config_job.LastHash,
        )
        msg = "Movement Controller: Source is same as last run"
        return await self._enqueue(config_exe, msg, trg_result, **kwargs)

    async def execute(self, config_exe: ExecutionConfig, **kwargs) -> MovementEvent:
        """Controler to execute Movement jobs"""
        trg_result = None
        if kwargs.get("key1", "pass") == "fail":
            raise MovementErrorHandling(self.ctx["job_id"])
        config_job = config_exe.JobConfig

        # avro objects
        if config_job.ActionType in (ActionTypes.CTI, ActionTypes.FSTB):
            avro_dto = await self._src_to_avro(config_job, **kwargs)
            if config_job.LastHash == avro_dto.BytesSHA256:
                return await self._src_is_same(config_exe, **kwargs)
            trg_result = await self._avro_to_trg(config_job, avro_dto)

        # binary objects
        if config_job.ActionType in (ActionTypes.BINC, ActionTypes.BINU):
            output = await self._src_to_binary(config_job)
            if config_job.LastHash == output.BytesSHA256:
                return await self._src_is_same(config_exe, **kwargs)
            trg_result = await self._binary_to_trg(config_job, output, **kwargs)

        msg = "Movement Controller: Completed run"
        return await self._enqueue(config_exe, msg, trg_result, **kwargs)
