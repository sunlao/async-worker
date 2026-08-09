from fastapi import APIRouter, HTTPException, Request, status
from shared.models.constants import EnqueueTypes
from shared.models.worker import EnqueueResponse
from worker.core.unique_job import DuplicateJobError

router = APIRouter()


@router.post(
    "/enqueue/{job_id}",
    response_model=EnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue(request: Request, job_id: int) -> EnqueueResponse:
    """Immediately enqueue a configured job by ID."""
    job = request.app.state.job.config(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"Message": f"Job Id: {job_id} is not configured"},
        )

    try:
        return await request.app.state.worker.enqueue(
            job,
            EnqueueTypes.MANUAL,
            delay_overide=0,
        )
    except DuplicateJobError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"Message": str(error)},
        ) from error
