from asyncio import gather
from fastapi import APIRouter, Request, status
from shared.models.api import ReadyResponse
from api.v1.helpers.health import Health

router = APIRouter()


@router.get("/ready", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
async def ready(request: Request) -> ReadyResponse:
    """Readiness check for api service which depends on a DB and Worker"""
    health = Health(request)
    db, redis, worker = await gather(
        health.db(),
        health.redis(),
        health.worker(),
    )
    return ReadyResponse(Database=db, Redis=redis, Worker=worker)
