from contextlib import suppress
from asyncio import wait_for, TimeoutError as ATimeoutError


class CliSourceError(RuntimeError):
    """Raised when the CLI source connector cannot produce valid rows."""


class Connector:
    """CLI connector to interface"""

    def __init__(self, context):
        self.sp = context["asubprocess"]
        self.platform = context.config_worker.Platform

    async def _kill(self, pid: int) -> None:
        if self.platform == "nt":
            command = f"taskkill /PID {pid} /T /F"
        else:
            command = f"kill -KILL -- -{pid}"
        proc = await self.sp.create_subprocess_shell(
            command, stdout=self.sp.DEVNULL, stderr=self.sp.DEVNULL
        )
        await proc.wait()

    async def execute(self, command: str, fail_on_stderr: bool = True) -> bytes:
        """Execute command and return raw stdout bytes."""
        options = {"stdout": self.sp.PIPE, "stderr": self.sp.PIPE}
        if self.platform != "nt":
            options["start_new_session"] = True
        proc = await self.sp.create_subprocess_shell(command, **options)
        try:
            stdout, stderr = await wait_for(proc.communicate(), timeout=600)
        except ATimeoutError as exc:
            with suppress(Exception):
                await self._kill(proc.pid)
                await proc.wait()
            raise CliSourceError("timeout after 600s") from exc
        if proc.returncode != 0:
            raise CliSourceError(
                f"Return code ({proc.returncode}) for command {command}"
            )
        if stderr and fail_on_stderr is True:
            raise CliSourceError(
                f"stderr not empty ({len(stderr)}) for command {command}"
            )
        return stdout
