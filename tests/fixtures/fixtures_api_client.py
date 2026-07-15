from pytest import fixture
from httpx import AsyncClient


@fixture
async def awork_api_client():
    test_api = "http://awork-api:80/api/v1/"
    async with AsyncClient(base_url=test_api, timeout=10) as client:
        yield client
