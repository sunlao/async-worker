from fastapi import APIRouter, __version__ as version, status, Request
from shared.models.api import InfoResponse

router = APIRouter()


@router.get(
    "/info",
    response_model=InfoResponse,
    status_code=status.HTTP_200_OK,
)
async def get_info(request: Request) -> InfoResponse:
    """Fast API and APP information"""
    app_version = request.app.state.app_version
    return InfoResponse(FastApiVersion=version, aworkVersion=app_version)
