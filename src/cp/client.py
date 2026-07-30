from shared.models.worker import EnqueueRequest, WorkerInit


class Client:
    def __init__(self, worker: WorkerInit) -> None:
        self.broker = worker.Broker

    async def startup(self) -> None:
        await self.broker.startup()

    async def shutdown(self) -> None:
        await self.broker.shutdown()

    async def enqueue(self, request: EnqueueRequest):
        if request.EnqueueGate:
            raise RuntimeError("Enqueue Gate Closed")
        task = self.broker.task_by_name(request.JobType)
        return (
            await task.kicker()
            .with_labels(job_id=request.Job.Config.Id)
            .kiq(request.Job)
        )
