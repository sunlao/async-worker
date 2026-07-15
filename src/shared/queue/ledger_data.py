from shared.models.api import LedgerData
from shared.models.constants import JobTypes


def serialize(job):
    config_info = job.args[0]
    config = config_info.Config
    src = None
    src_type = None
    trg = None
    trg_type = None
    if config_info.Type == JobTypes.MOVEMENT:
        src = config.Source
        src_type = config.SourceType
        trg = config.Target
        trg_type = config.TargetType
    return LedgerData(
        JobType=config_info.Type,
        JobId=config.Id,
        Name=config.Name,
        ActionType=config.ActionType,
        Source=src,
        SourceType=src_type,
        Target=trg,
        TargetType=trg_type,
        Cmd=config.Cmd,
        StartUp=config.StartUp,
        RunOnce=config.RunOnce,
        RunNext=str(config.RunNext),
        JobTry=job.job_try,
        RunId=job.job_id,
        EnqueueTime=job.enqueue_time,
        StartTime=job.start_time,
        FinishTime=job.finish_time,
        Status=job.result.Event.Status,
        Message=job.result.Event.Message,
    )
