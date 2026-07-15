from asyncio import sleep
from datetime import UTC
from shared.models.worker import ExecutionConfig, MovementConfig
from shared.models.constants import ActionTypes


async def test_controller(worker_ctx, controller_movement, db_get_one):
    config_log = worker_ctx["config_log"]
    worker_ctx["job_id"] = "test_run_id_103"
    target = "raw.hello_test_controller"
    arg = target
    row = await db_get_one("hello_audit", arg)
    dtl = {"hash": None}
    if row is not None:
        dtl = {"hash": row[0].hex()}

    config_move = MovementConfig(
        Id=104,
        Name="TestContoller-hello",
        ActionType=ActionTypes.CTI,
        Source="hello_test_controller",
        SourceType="cli",
        Cmd=(
            'echo \'{"source_word":"word$RANDOM","source'
            '_time":"\'$(date -u +"%Y-%m-%dT%H:%M:%SZ")\'"}\''
        ),
        Target=target,
        TargetType="pg",
        Delay=0,
        Retry=0,
        StartUp=False,
        RunOnce=True,
        LastHash=dtl["hash"],
    )
    config: ExecutionConfig[MovementConfig] = ExecutionConfig(
        Start=config_log.Now(UTC),
        StartCounter=config_log.TimeCounter(),
        JobConfig=config_move,
    )
    kwarg = {"kwargs": {"key1": "pass"}}
    async with worker_ctx["db"].client() as conn:
        response = await controller_movement(worker_ctx, conn).execute(config, **kwarg)
    assert response.Status
    await sleep(3)

    print("\n\n** Sleep to let db and job get in sync\n\n")
    row = await db_get_one("hello_test_controller")
    assert row[0] == 1
