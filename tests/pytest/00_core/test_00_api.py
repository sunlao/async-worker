async def test_awork(awork_api_client):
    response = await awork_api_client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert response.json() == {"Message": "AsyncServ API Service is up!"}

