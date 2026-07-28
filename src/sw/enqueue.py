import asyncio
from sw import broker, example
from sw.status import Status

async def main() -> None:
    await broker.startup()

    task = await (
        example
        .kicker()
        .with_labels(job_id=1)
        .kiq(1)
    )

    status = Status()
    print(f"enqueue: {task.task_id}")
    print(f"in work: {await status.job_id_in_work(broker, 1)}")
    result = await task.wait_result(timeout=60)
    print(result)
    await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
