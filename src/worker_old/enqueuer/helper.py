from shared.models.constants import JobTypes
from shared.models.worker import JobConfig


def delay(re_enqueue: bool, config: JobConfig, job_type: JobTypes) -> int:
    if job_type == JobTypes.ADMIN:
        return 0 if re_enqueue is False else config.Config.Delay
    if job_type == JobTypes.MOVEMENT:
        return 0 if re_enqueue is False else config.Config.Delay
    raise RuntimeError(f"Job Type: {job_type} - Not Supported ")
