# pylint: disable=duplicate-code
from asyncio import sleep, timeout

job_id = 103


async def test_enqueue_fail(awork_api_client):
    response = await awork_api_client.post(f"enqueue/{job_id}")
    doc = response.json()
    assert response.status_code == 202
    run_id = doc["RunID"]
    status = "n/a"
    async with timeout(300):
        while status != "complete":
            await sleep(5)
            response = await awork_api_client.get(f"runs/{run_id}")
            doc = response.json()
            status = doc["Status"]
    assert status == "complete"
    assert doc["Info"]["Event"]["Status"] is False
    assert (
        doc["Error"]["ExceptionMessage"]
        == f"{run_id} failed as part of Movement Controller error handling"
    )
