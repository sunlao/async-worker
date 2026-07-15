from pytest import fixture
from shared.models.constants import ActionTypes, SourceTypes, TargetTypes
from shared.models.worker import SerializeInput, MovementConfig


@fixture(scope="session")
def tstc_pg_job():
    return MovementConfig(
        Id=1003,
        Name="CitiesLoad",
        ActionType=ActionTypes.FSTB,
        Source="cities1000.txt",
        SourceType=SourceTypes.CLI,
        Cmd="",
        Target="raw.cities",
        TargetType=TargetTypes.PG,
        Delay=0,
        Retry=10,
        StartUp=False,
        RunOnce=True,
        LastHash="tbd",
    )


@fixture(scope="session")
def tstc_pg_kwarg():
    return {
        "column_filters": [
            "geonameid",
            "asciiname",
            "country_code",
            "admin1_code",
            "timezone",
            "modification_date",
        ]
    }


@fixture(scope="session")
def avro_searilize():
    return SerializeInput(
        Rows="tdb",
        Name="cities1000.txt",
        Schema="tbd",
    )
