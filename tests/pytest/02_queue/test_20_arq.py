# pylint: disable=protected-access
from asyncio import sleep
from shared.models.worker import Health


async def test_health(arq_client):
    assert Health.model_validate(await arq_client.health())


async def test_enqueue_methods(arq_client, job_100):
    # assert enqueue, queued, completed, _in_progress, run_info
    job = await arq_client.enqueue(job_100)
    job_id = job.job_id
    queued_jobs = await arq_client.queued()
    queued_job_ids = [j.job_id for j in queued_jobs]
    assert job_id in queued_job_ids
    completed_jobs = await arq_client.completed()
    completed_job_ids = [j.job_id for j in completed_jobs]
    # job 100 will sleeps for 3 seconds
    assert job_id not in completed_job_ids
    status = "unknown"
    while status != "complete":
        job = arq_client.run_info(job_id)
        status = await job.status()
        if status == "complete":
            break
        # job 100 will sleeps for 3 seconds
        await sleep(1)
    info = await job.info()
    assert info.result.Event.Status is True
