from shared.helper.target_audit_detail import TargetAuditDetail
from shared.models.worker import JobConfig, MovementConfig


async def test_one(arq_client, db, reader):
    tad = TargetAuditDetail(arq_client, db)
    job_info = reader.config(102)
    new_job = await tad.update_job(job_info)
    JobConfig.model_validate(new_job)
    MovementConfig.model_validate(new_job.Config)
