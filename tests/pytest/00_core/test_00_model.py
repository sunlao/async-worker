# tests/test_model_kinds.py
import enum
import importlib
import inspect
import pkgutil
import typing as t
import pytest
from pydantic import BaseModel
import shared.models as models_pkg
from shared.models.policy import DTO_CONFIG, DTO_EDGE_CONFIG

# ONLY classes allowed to use the ASGI/edge config:
EDGE_CONFIG_ALLOWED: set[str] = {
    "shared.models.api.ASGIEvent",
    "shared.models.log.Config",
    "shared.models.db.DBStartUpContext",
    "shared.models.db.DBConnInput",
    "shared.models.db.DBConnection",
    "shared.models.worker.HandleExecution",
    "shared.models.worker.Lifecycle",
    "shared.models.admin.QuiesceQueue",
}


def iter_defined_classes(root_pkg) -> list[type]:
    out: list[type] = []
    for _, modname, _ in pkgutil.walk_packages(
        root_pkg.__path__, root_pkg.__name__ + "."
    ):
        m = importlib.import_module(modname)
        for _, cls in inspect.getmembers(m, inspect.isclass):
            if cls.__module__ == m.__name__:
                out.append(cls)
    return out


def fqcn(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def is_strenum(cls: type) -> bool:
    return issubclass(cls, enum.StrEnum)


def is_named_tuple(cls: type) -> bool:
    return issubclass(cls, t.NamedTuple)


def is_dto(cls: type) -> bool:
    return issubclass(cls, BaseModel)


ALL_CLASSES = iter_defined_classes(models_pkg)


# 1) Every class must be either StrEnum or DTO (no third bucket)
@pytest.mark.parametrize("cls", ALL_CLASSES, ids=fqcn)
def test_every_model_is_strenum_or_dto(cls: type):
    assert (
        is_strenum(cls) or is_named_tuple or is_dto(cls)
    ), f"{fqcn(cls)} must be StrEnum or DTO"


# 2) DTOs must use the right config (enums don’t have one)
@pytest.mark.parametrize("cls", [c for c in ALL_CLASSES if is_dto(c)], ids=fqcn)
def test_dto_config_and_whitelist(cls: type):
    cfg = getattr(cls, "model_config", None)
    name = fqcn(cls)

    # Special-case: LedgerData is allowed to extend DTO_CONFIG with populate_by_name=True
    if name == "shared.models.admin.LedgerData":
        base = DTO_CONFIG
        # must match all base items
        assert all(cfg.get(k) == v for k, v in base.items())
        # and only add this one key
        extra_keys = set(cfg.keys()) - set(base.keys())
        allowed_extras = {"populate_by_name", "validate_by_name", "validate_by_alias"}
        assert extra_keys == allowed_extras
    else:
        assert cfg in (
            DTO_CONFIG,
            DTO_EDGE_CONFIG,
        ), f"{fqcn(cls)} must use DTO_CONFIG or DTO_EDGE_CONFIG"
        if cfg == DTO_EDGE_CONFIG:
            assert (
                fqcn(cls) in EDGE_CONFIG_ALLOWED
            ), f"{fqcn(cls)} uses EDGE_CONFIG_ALLOWED but is not whitelisted"
        if cfg == DTO_CONFIG:
            assert not bool(
                cfg.get("arbitrary_types_allowed")
            ), f"{fqcn(cls)} must not enable arbitrary_types_allowed"


# 3) Inheritance rule: allow BaseModel, or BaseModel+Generic for generic DTOs
@pytest.mark.parametrize("cls", [c for c in ALL_CLASSES if is_dto(c)], ids=fqcn)
def test_dto_inheritance_rules(cls: type):
    bases = cls.__bases__
    if t.Generic in bases:
        assert bases == (
            BaseModel,
            t.Generic,
        ), f"{fqcn(cls)} must inherit only from (BaseModel, Generic)"
    else:
        assert bases == (BaseModel,), f"{fqcn(cls)} must inherit only from BaseModel"
