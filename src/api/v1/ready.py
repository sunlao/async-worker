from asyncio import gather
from fastapi import APIRouter, Request, status
from shared.models.api import ReadyResponse
from api.v1.helpers.health_checks import HealthCheck

router = APIRouter()


@router.get("/ready", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
async def ready(request: Request) -> ReadyResponse:
    """Readiness check for api service which depends on a DB and Worker"""
    db_check, worker_check = await gather(
        HealthCheck().db(request),
        HealthCheck().worker(request),
    )
    return ReadyResponse(DBCheck=db_check, WorkerCheck=worker_check)
