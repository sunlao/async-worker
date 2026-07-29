import asyncio
from sw import broker, example, redis


async def main() -> None:
    await broker.startup()
    job_id = 1
    key = f"taskiq:active:{job_id}"
    reserved = await redis.set(key, "reserved", nx=True)

    if not reserved:
        print(f"already active: {job_id}")
        await broker.shutdown()
        await redis.aclose()
        return
    try:
        task = await example.kicker().with_labels(job_id=job_id).kiq(job_id)
        print(f"enqueue: {task.task_id}")
        result = await task.wait_result(timeout=60)
        print(result)
    except Exception:
        await redis.delete(key)
        raise
    await broker.shutdown()
    await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
