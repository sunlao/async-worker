# edge-allow: pathlib, open, httpx
from pathlib import Path
from hashlib import sha256
from httpx import HTTPStatusError
from fastapi import status
from shared.models.constants import ActionTypes
from shared.models.worker import BinaryOutput


class Connector:
    # pylint: disable=duplicate-code
    def __init__(self, ctx):
        self.ctx = ctx
        cwd_parent = Path(self.ctx["data_dir"])
        self.zip_path = cwd_parent.joinpath("zip")
        self.ready_path = cwd_parent.joinpath("ready")
        self.http_client = ctx["http_client"]

    async def download(
        self, command: str, name: str, action_type: ActionTypes
    ) -> BinaryOutput:
        file_hash = sha256()
        size_bytes = 0
        async with self.http_client.stream("GET", command) as response:
            response.raise_for_status()
            path = None
            if action_type == ActionTypes.BINC:
                path = self.zip_path.joinpath(name)
            if action_type == ActionTypes.BINU:
                path = self.ready_path.joinpath(name)
            if path is None:
                raise RuntimeError(f"Action type: {action_type} is not supported")
            with open(path, "wb") as file:
                async for chunk in response.aiter_bytes(chunk_size=1 << 20):  # 1 MiB
                    if not chunk:
                        continue
                    file.write(chunk)
                    file_hash.update(chunk)
                    size_bytes += len(chunk)
        return BinaryOutput(BytesSHA256=file_hash.hexdigest(), BytesLen=size_bytes)

