from fastapi import APIRouter, Request, status
from shared.models.worker import ReportState


router = APIRouter()


@router.get(
    "/state",
    response_model=ReportState,
    status_code=status.HTTP_200_OK,
)
async def get_state(request: Request) -> ReportState:
    """Worker queue state"""
    return await request.app.state.worker.state()