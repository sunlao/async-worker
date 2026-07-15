from re import compile as recompile
from shared.models.constants import UserContext
from shared.models.log import Config
from shared.models.config import DBSecrets, Redis


def test_app_version(locker):
    config_awork = locker.awork()
    semantic_version_check = recompile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )
    assert bool(semantic_version_check.match(config_awork.AppVersion))


def test_log(locker):
    config = locker.log()
    assert isinstance(config, Config)


def test_db(locker):
    config = locker.db(UserContext.APP)
    assert isinstance(config, DBSecrets)


def test_db_config(locker):
    config = locker.redis()
    assert isinstance(config, Redis)
