import asyncio
from sw import broker, example


async def main() -> None:
    await broker.startup()
    task = await (
        example
        .kicker()
        .with_labels(job_id=1)
        .kiq(1)
    )
    print(f"enqueue: {task.task_id}")
    result = await task.wait_result(timeout=60)
    print(result)
    await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
