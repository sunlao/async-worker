async def test_api_ready(awork_api_client):
    response = await awork_api_client.get("ready")
    assert response.status_code == 200
    json_dict = response.json()
    assert json_dict["DBCheck"] is True
    assert json_dict["WorkerCheck"] is True
