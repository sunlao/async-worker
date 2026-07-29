import asyncio
from sw import broker, example, redis


async def main() -> None:
    await broker.startup()
    job_id = 1
    active = await redis.exists(f"taskiq:active:{job_id}")
    print(f"in work: {bool(active)}")
    task = await example.kicker().with_labels(job_id=job_id).kiq(job_id)
    print(f"enqueue: {task.task_id}")
    result = await task.wait_result(timeout=60)
    print(result)
    await broker.shutdown()
    await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
