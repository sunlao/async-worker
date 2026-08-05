from taskiq import AsyncBroker, TaskiqDepends, TaskiqState
from shared.models.constants import JobTypes
from shared.models.worker import HelloConfig, JobConfig
from worker.handler.hello import Hello


async def hello(
    config: JobConfig[HelloConfig], context: TaskiqState = TaskiqDepends()
) -> None:
    await Hello(context).handle(config)


def register(queue: AsyncBroker) -> AsyncBroker:
    queue.task(task_name=JobTypes.HELLO)(hello)
    return queue