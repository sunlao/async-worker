from shared.log.helpers.error import Error
from shared.models.constants import PathParts


path_part = PathParts.TESTS
file = "test_01_log.py"
bad_function = "trigger_error"
calling_function = "test_call_trigger"
error_name = "DemoError"


class DemoError(Exception):
    def __init__(self, value: str, message: str):
        super().__init__(f"Demo Error!: The {value} was {message}")


def trigger_error():
    raise DemoError("error", "triggered")


def test_call_trigger():
    trace_back_nfo = None
    try:
        trigger_error()
    except DemoError as e:
        trace_back_nfo = Error().trace_back_nfo(exc_class=e, path_part=path_part)
    assert trace_back_nfo.Exception.endswith(error_name)
    assert trace_back_nfo.LastTBFile.endswith(file)
    assert path_part in trace_back_nfo.LastTBFile
    assert trace_back_nfo.LastTBFunction in {bad_function, calling_function}
    assert trace_back_nfo.LastTBLineNo > 0
    assert trace_back_nfo.TBCount > 1
    assert len(trace_back_nfo.Last5TB) > 1


def test_no_path_parts():
    trace_back_nfo = None
    try:
        trigger_error()
    except DemoError as e:
        trace_back_nfo = Error().trace_back_nfo(exc_class=e, path_part=PathParts.SRC)
    assert trace_back_nfo.LastTBFile == "<unknown>"
    assert trace_back_nfo.LastTBFunction == "<unknown>"
    assert trace_back_nfo.LastTBLineNo == 0
