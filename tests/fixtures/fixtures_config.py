from pytest import fixture
from shared.config.locker import Locker
from shared.config.reader import Reader, ReaderConfig


@fixture(scope="session", name="locker")
def f_locker():
    return Locker()


@fixture(scope="session")
def redis_config(locker):
    return locker.redis()


@fixture(scope="session", name="config_log")
def f_config_log(locker):
    return locker.log()


@fixture(scope="session", name="config_awork")
def f_config_awork(locker):
    return locker.awork()


@fixture(scope="session", name="config_worker")
def f_config_worker(locker):
    return locker.worker()


@fixture(name="reader")
def f_reader(locker):
    awork = locker.awork()
    reader = ReaderConfig(JobPath=awork.JobPath, JobVersion=awork.JobVersion)
    return Reader(reader)
