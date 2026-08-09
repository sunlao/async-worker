from taskiq import AsyncBroker, TaskiqDepends, TaskiqState
from shared.models.constants import JobTypes
from shared.models.worker import AdminConfig, HelloConfig, JobConfig
from worker.handler.admin import Admin
from worker.handler.hello import Hello


async def admin(
    config: JobConfig[AdminConfig], context: TaskiqState = TaskiqDepends()
) -> None:
    await Admin(context).handle(config)


async def hello(
    config: JobConfig[HelloConfig], context: TaskiqState = TaskiqDepends()
) -> None:
    await Hello(context).handle(config)


def register(queue: AsyncBroker) -> AsyncBroker:
    queue.task(task_name=JobTypes.ADMIN)(admin)
    queue.task(task_name=JobTypes.HELLO)(hello)
    return queue
