import asyncio
from sw import broker, example


async def main() -> None:
    await broker.startup()
    task = await example.kiq(1)
    print(task, flush=True)
    print(type(task), flush=True)
    print(vars(task), flush=True)    
    print(f"enqueue: {task.task_id}")
    await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
