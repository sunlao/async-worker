from pytest import raises
from shared.config.reader import Reader
from shared.models.constants import ActionTypes, JobTypes, SourceTypes, TargetTypes


def test_start_configs(worker_ctx):
    name = "Test-Startup-Normal"
    reader = worker_ctx["reader"]
    job_configs = reader.startup_configs(JobTypes.MOVEMENT)
    assert len(job_configs) == 2
    for job_config in job_configs:
        assert job_config.Type == JobTypes.MOVEMENT
        config = job_config.Config
        if config.Name == name:
            assert config.ActionType == ActionTypes.CTI
            assert config.Source == "src1"
            assert config.SourceType == SourceTypes.CLI
            assert config.Cmd == "this is comand 1"
            assert config.Target == "trg1"
            assert config.TargetType == TargetTypes.PG
            assert config.Retry == 1
            assert config.Delay == 1
            assert config.RunOnce is False
            assert job_config.KWARGS == {"Hello": "movement"}
        assert config.StartUp is True


def test_config(worker_ctx):
    reader = worker_ctx["reader"]
    job_config = reader.config(103)
    assert job_config.Type == JobTypes.XFORM
    config = job_config.Config
    assert config.Name == "Test-XForm-Event1"
    assert config.ActionType == ActionTypes.RUN
    assert config.Cmd == "xform-service-url"
    assert config.Retry == 3
    assert config.Delay == 86400
    assert config.StartUp is False
    assert config.RunOnce is True
    assert job_config.KWARGS == {"Hello": "XForm1"}


def test_validation(worker_ctx):
    config = worker_ctx["config_reader_bad"]
    with raises(RuntimeError) as err:
        Reader(config)
    msg = "Config is not valid for ['Ids', 'Names', 'Source:Target', 'next']"
    assert str(err.value) == msg


def test_config_enqueue_next(worker_ctx):
    reader = worker_ctx["reader"]
    job_config = reader.config(104)
    config = job_config.Config
    assert config.RunNext == (101, 102, 103)
