# pylint: disable=protected-access
from asyncio import sleep


async def test_at_most_one_active_enqueue(arq_client, job_100):
    q1 = await arq_client.queued(100)
    if len(q1) == 0:
        run = await arq_client.enqueue(job_100)
        assert run.job_id is not None
    q2 = await arq_client.queued(100)
    q_cnt = len(q2)
    assert q_cnt > 0
    ex2_flg = 0
    # job 100 will sleep 3 seconds when enqueued
    while q_cnt > 0:
        q2 = await arq_client.queued(100)
        q_cnt = len(q2)
        if q_cnt == 0:
            break
        run2 = await arq_client.enqueue(job_100)
        assert run2 is None
        await sleep(1)
        ex2_flg = 1
    # assert enqueue was attempted after break while queued cnt > 1 at least once
    assert ex2_flg == 1
