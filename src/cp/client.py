async def enqueue(self, request: EnqueueRequest) -> str | None:
    if request.EnqueueGate:
        raise RuntimeError("Enqueue Gate Closed")

    job_id = request.Job.Config.Id

    if await self.unique_job.exists(job_id):
        return None

    task = await (
        self.broker
        .task_by_name(request.JobType)
        .kicker()
        .with_labels(job_id=job_id)
        .kiq(request.Job)
    )

    return task.task_id