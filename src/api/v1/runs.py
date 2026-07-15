from fastapi import APIRouter, Request, status
from api.v1.helpers.run_serializer import RunSerializer
from shared.models.api import RunResponse, RunsResponse


router = APIRouter()


@router.get(
    "/runs/{job_id}", response_model=RunResponse, status_code=status.HTTP_200_OK
)
async def get_run_by_id(request: Request, job_id: str) -> RunResponse:
    """Job Detail from ARQ"""
    dto = await RunSerializer(request).run(str(job_id))
    return dto


@router.get("/runs", response_model=RunsResponse, status_code=status.HTTP_200_OK)
async def get_runs(request: Request) -> RunsResponse:
    """List of all jobs from ARQ with job detail information and error counts"""
    dto = await RunSerializer(request).runs()
    errors = sum(1 for x in dto.Runs if x.Error)
    return RunsResponse(Runs=dto.Runs, Errors=errors)
