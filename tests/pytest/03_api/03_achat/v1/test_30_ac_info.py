from shared.models.api import InfoResponse


async def test_api_info(awork_api_client):
    response = await awork_api_client.get("info")
    assert response.status_code == 200
    assert InfoResponse.model_validate(response.json())
