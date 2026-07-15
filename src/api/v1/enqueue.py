from fastapi import APIRouter, Request, status, HTTPException
from shared.helper.target_audit_detail import TargetAuditDetail
from shared.models.api import EnqueueResponse
from shared.models.worker import EnqueueRequest
from shared.models.constants import JobTypes

router = APIRouter()


@router.post(
    "/enqueue/{job_id}",
    response_model=EnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
# pylint: disable=too-many-locals
async def enqueue(request: Request, job_id: int) -> EnqueueResponse:
    """Enqueue Jobs on worker by id from job yml"""
    arq = request.app.state.arq_client
    db = request.app.state.db
    reader = request.app.state.reader
    job_info = reader.config(job_id)
    gate = request.app.state.enqueue_gate
    job = None

    if job_info.Type == JobTypes.MOVEMENT:
        updt = await TargetAuditDetail(arq, db).update_job(job_info)
        job = await arq.enqueue(
            EnqueueRequest(JobType=job_info.Type, Job=updt, EnqueueGate=gate)
        )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "Message": f"Job Id: {job_info.Config.Id} already enqueued",
                "RunID": None,
            },
        )
    run_id = job.job_id

    return EnqueueResponse(
        RunID=run_id,
        Message=f"Enqueue success for job {job_info.Config.Id}",
        Status=await job.status(),
    )
