from datetime import timedelta
from taskiq import TaskiqState
from shared.models.worker import JobConfig

class Client:
    async def enqueue(
        self,
        state: TaskiqState,
        job: JobConfig,
        job_id: int,
        delay: int | None,
    ):
        if state.enqueue_gate:
            raise RuntimeError("Enqueue Gate Closed")

        dispatcher = state.queue.task_by_name(job.Type)
        kicker = dispatcher.kicker().with_labels(job_id=job_id)

        if delay is not None:
            return await kicker.schedule_by_interval(
                state.delay_source,
                timedelta(seconds=delay),
                job=job,
            )

        return await kicker.kiq(job=job)