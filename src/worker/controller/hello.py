from datetime import UTC
from worker.connector.io.connector import Connector as CLI
from shared.models.constants import ConnectorTypes, ResourceTypes
from shared.models.worker import (
    HelloEvent,
    ExecutionConfig,
    HelloConfig,
    HelloJobResult,
    ConnectionProfile,
    ConnecterDBPoolInput,
)
from worker.connector.api.connector import Connector as API
from worker.connector.db.pool import Pool
from worker.controller.post_process import PostProcess


class Hello:
    """Hello Controller demonstrates worker functionality"""

    def __init__(self, context):
        self.context = context
        self.log = self.context["config_log"]
        self.gate = context["enqueue_gate"]
        self.connection = context.connection
        self.post_process = PostProcess(self.context)

    async def _api_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        pass

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
            check = {"abc":False, "abc_def": False}
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
                return HelloJobResult(Pass=True)
            return HelloJobResult(Pass=False)
        raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")

    async def _io_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        pass

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

    async def execute(self, exe: ExecutionConfig[HelloConfig], **kwargs) -> HelloEvent:
        """Controller to execute Hello jobs Action Types by controller"""
        profile = self.connection.profile(exe.JobConfig.ConnectionProfile)
        connector_type = profile.ConnectorType
        if connector_type == ConnectorTypes.DB:
            result1 = await self._db_actions(exe, profile)
            print(f"result: {result1}")
        if connector_type == ConnectorTypes.IO:
            result2 = await self._io_actions(exe, profile, **kwargs)
        if connector_type == ConnectorTypes.API:
            result3 = await self._api_actions(exe, profile, **kwargs)
        result = HelloJobResult(Pass=True)
        self.post_process.execute(exe.JobId)
        return self._event(exe, "g2g", result)
