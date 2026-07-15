from asyncio import gather
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from shared.models.api import RunResponse, Runs
from shared.models.constants import ArqStatus


class RunSerializer:
    """Use arq client from the edge to serialize job run info to DTO"""

    def __init__(self, request: Request):
        self.arq = request.app.state.arq_client

    @staticmethod
    def _clean_status(status: str) -> str:
        s = str(status).lower()
        return s.split(".", maxsplit=1)[-1]

    @staticmethod
    def _custom_encode(info):
        return jsonable_encoder(info, custom_encoder={type: lambda t: t.__name__})

    async def _run_response(self, job) -> RunResponse:
        try:
            job_status = self._clean_status(await job.status())
        except Exception:  # pylint: disable=broad-except
            return RunResponse(
                RunID=job.job_id, Status=ArqStatus.UNKNOWN, Info=None, Error=None
            )
        if job_status != "complete":
            return RunResponse(
                RunID=job.job_id, Status=job_status, Info=None, Error=None
            )
        info = self._custom_encode(await job.info())
        result = info.get("result") or {}
        error = result.pop("Error", None)
        if error is not None or result == {}:
            return RunResponse(
                RunID=job.job_id, Status=job_status, Info=result, Error=error
            )
        return RunResponse(RunID=job.job_id, Status=job_status, Info=result, Error=None)

    def _completed(self, job) -> RunResponse:
        if job.result.Event.Status is True:
            info = self._custom_encode(job.result)
            return RunResponse(
                RunID=job.job_id, Status="complete", Info=info, Error=None
            )
        info = self._custom_encode(job.result)
        error = self._custom_encode(info.pop("Error"))
        return RunResponse(RunID=job.job_id, Status="complete", Info=info, Error=error)

    async def run(self, run_id: str) -> RunResponse:
        job = self.arq.run_info(run_id)
        response = await self._run_response(job)
        return response

    async def runs(self) -> Runs:
        queued, completed = await gather(self.arq.queued(), self.arq.completed())
        run_completed = [self._completed(j) for j in completed]
        ids = [j.job_id for j in completed]
        run_queued = await gather(
            *[self._run_response(j) for j in queued if j.job_id not in ids]
        )
        return Runs(Runs=tuple(run_completed + run_queued))
