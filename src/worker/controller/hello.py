from datetime import UTC
from worker.connector.io.connector import Connector as io
from shared.models.api import ReadyResponse
from shared.models.constants import ConnectorTypes, ResourceTypes, ActionTypes
from shared.models.worker import (
    HelloEvent,
    ExecutionConfig,
    HelloConfig,
    HelloJobResult,
    ConnectionProfile,
    ConnecterDBPoolInput,
)
from worker.connector.api.edge import Edge
from worker.connector.db.pool import Pool


class Hello:
    """Hello Controller demonstrates worker functionality"""

    def __init__(self, context):
        self.context = context
        self.log = self.context["config_log"]
        self.gate = context["enqueue_gate"]
        self.connection = context.connection
        self.post_process = PostProcess(self.context)
        self.api_port = context.config_worker.ApiPort
        self.asleep = context.asleep

    async def _api_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ) -> HelloJobResult:
        if prof.ResourceType != ResourceTypes.API_EDGE:
            raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")
        if exe.JobConfig.ActionType != ActionTypes.GET:
            raise RuntimeError(f"Unsupported ActionType: {exe.JobConfig.ActionType}")
        if exe.JobConfig.Cmd is None:
            raise RuntimeError("Cmd is required for GET")
        url = exe.JobConfig.Cmd.format(API_PORT=self.api_port)
        print(f"url: {url}")
        self.api_port
        response = await Edge(self.context).get(url)
        ready = ReadyResponse.model_validate(response.json())
        if ready.Database is True and ready.Redis is True and ready.Worker is True:
            return HelloJobResult(
                Pass=True, Message="Database, Redis and Worker are ready"
            )
        return HelloJobResult(
            Pass=False, Message="Database, Redis and Worker are not ready"
        )

    @staticmethod
    def _db_check(check, result, name):
        if name == "hello_select_count_abc_canary" and result[0] == 1:
            check["abc"] = True
        if name == "hello_select_count_abc_def_canary" and result[0] == 2:
            check["abc_def"] = True
        return check

    async def _db_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile
    ):
        if prof.ResourceType == ResourceTypes.DB_EDGE:
            check = {"abc": False, "abc_def": False}
            queries = exe.JobConfig.Queries
            pass_kwargs = {}
            for q in queries:
                input = ConnecterDBPoolInput(
                    ActionType=q.ActionType, SQLName=q.Name, Args=q.Args
                )
                result = await Pool(self.context).execute(input, **pass_kwargs)
                check = self._db_check(check, result, q.Name)
                if q.PassResultFlag is True:
                    pass_kwargs = {"args_orveride": self._pass_kwargs(result)}
                else:
                    pass_kwargs = {}
            if check["abc"] is True and check["abc_def"] is True:
                return HelloJobResult(Pass=True, Message="DB Checks pass after insert")
            return HelloJobResult(Pass=False, Message="DB Checks failed after insert")
        raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")

    async def _io_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile
    ) -> HelloJobResult:
        if prof.ResourceType != ResourceTypes.ASUBPROCESS:
            raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")
        if exe.JobConfig.ActionType != ActionTypes.SUBPROCESS:
            raise RuntimeError(f"Unsupported ActionType: {exe.JobConfig.ActionType}")
        if exe.JobConfig.Cmd is None:
            raise RuntimeError("Cmd is required for SUBPROCESS")
        if exe.JobId == 102:
            print(f"JobId: {exe.JobId}")
            await self.asleep(5)
        response = await io(self.context).execute(exe.JobConfig.Cmd)
        if response.ReturnCode == 0:
            return HelloJobResult(Pass=True, Message=response.Message)
        return HelloJobResult(Pass=False, Message=response.Error)

    def _event(
        self, exe: ExecutionConfig[HelloConfig], msg: str, result: HelloJobResult
    ) -> HelloEvent:
        return HelloEvent(
            JobId=exe.JobId,
            JobName=exe.JobConfig.Name,
            ConnectionProfile=exe.JobConfig.ConnectionProfile,
            Status=True,
            Message=msg,
            Start=exe.Start,
            End=self.log.Now(UTC),
            DurationMs=int((self.log.TimeCounter() - exe.StartCounter) * 1000),
            Result=result,
        )

    @staticmethod
    def _pass_kwargs(result) -> tuple[object, ...]:
        return tuple(value for row in result for value in row)

    async def execute(self, exe: ExecutionConfig[HelloConfig]) -> HelloEvent:
        """Controller to execute Hello jobs Action Types by controller"""
        profile = self.connection.profile(exe.JobConfig.ConnectionProfile)
        connector_type = profile.ConnectorType
        if connector_type == ConnectorTypes.DB:
            result = await self._db_actions(exe, profile)
        if connector_type == ConnectorTypes.IO:
            result = await self._io_actions(exe, profile)
        if connector_type == ConnectorTypes.API:
            result = await self._api_actions(exe, profile)
        return self._event(exe, "g2g", result)
