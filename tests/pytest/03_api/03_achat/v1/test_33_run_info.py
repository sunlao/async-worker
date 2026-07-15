# pylint: disable=duplicate-code
from asyncio import sleep, timeout
from shared.helper.target_audit_detail import TargetAuditDetail


job_id = 102


async def test_detail(awork_api_client, api_request, reader):
    job_info = reader.config(102)
    response = await awork_api_client.post(f"enqueue/{job_id}")
    assert response.status_code == 202
    doc = response.json()
    run_id1 = doc["RunID"]
    print(f"****runid: {run_id1}")
    response = await awork_api_client.post(f"enqueue/{job_id}")
    assert response.status_code == 409
    status = "?"
    async with timeout(300):
        while status != "complete":
            await sleep(2)
            response = await awork_api_client.get(f"runs/{run_id1}")
            doc = response.json()
            status = doc["Status"]
    assert status == "complete"
    response = await awork_api_client.post(f"enqueue/{job_id}")
    assert response.status_code == 202
    doc = response.json()
    run_id2 = doc["RunID"]
    print(f"****runid: {run_id2}")
    status = "?"
    async with timeout(300):
        while status != "complete":
            await sleep(2)
            response = await awork_api_client.get(f"runs/{run_id2}")
            doc = response.json()
            status = doc["Status"]
    assert status == "complete"
    response = await awork_api_client.post("enqueue/102")
    assert response.status_code == 202
    doc = response.json()
    run_id3 = doc["RunID"]
    print(f"****runid: {run_id3}")
    status = "?"
    async with timeout(300):
        while status != "complete":
            await sleep(2)
            response = await awork_api_client.get(f"runs/{run_id3}")
            doc = response.json()
            status = doc["Status"]
    assert status == "complete"

    tad = TargetAuditDetail(api_request.app.state.arq_client, api_request.app.state.db)
    new_job = await tad.update_job(job_info)
    assert new_job.Config.LastHash is not None
