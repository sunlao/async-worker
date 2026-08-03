# pylint: disable=import-outside-toplevel
# pylint: disable=duplicate-code
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/flush")
async def coverage_save(request: Request):
    """Exists to support code coverage
    - execute in env ci only"""
    log = request.app.state.config_log
    env = log.Environment
    if env == "ci":
        from coverage import Coverage

        cov = Coverage.current()
        if cov:
            cov.save()
        d = cov.get_data()
        measured = list(d.measured_files())
        data_file = d.data_filename()
        return JSONResponse(
            {
                "saved": True,
                "measured_files": len(measured),
                "sample": measured[:5],
                "data_file": data_file,
            },
            status_code=200,
        )
    return JSONResponse({"saved": False}, status_code=200)
