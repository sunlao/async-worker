from uuid import uuid4
from typing import Optional
import asyncio.subprocess as asp
from asyncio import wait_for, TimeoutError as ATimeoutError
from shared.models.api import AdminExecutionResults


def _text(b: Optional[bytes]) -> str:
    return b.decode("utf-8", "replace").strip() if b else ""


async def _run(cmd) -> RunResults:
    proc = await asp.create_subprocess_shell(
        cmd,
        stdout=asp.PIPE,
        stderr=asp.PIPE,
    )
    try:
        out, err = await wait_for(proc.communicate(), timeout=30)
    except ATimeoutError:
        proc.kill()
        out, err = await proc.communicate()
        return RunResults(ReturnCode=124, Output=_text(out), Error=_text(err))
    return RunResults(
        ReturnCode=proc.returncode or 0, Output=_text(out), Error=_text(err)
    )


async def sigterm():
    cmd = (
        'docker kill --signal=SIGTERM $(docker ps -q --filter "label=com.'
        'docker.compose.service=worker")'
    )
    results = await _run(cmd)
    return AdminExecutionResults(
        ExecutionId=uuid4(),
        Code=results.ReturnCode,
        Message=results.Output,
        Error=results.Error,
    )


async def restart():
    cmd = (
        'docker start $(docker ps -a -q --filter "label=com.docker.compose.'
        'service=worker")'
    )
    results = await _run(cmd)
    return AdminExecutionResults(
        ExecutionId=uuid4(),
        Code=results.ReturnCode,
        Message=results.Output,
        Error=results.Error,
    )
