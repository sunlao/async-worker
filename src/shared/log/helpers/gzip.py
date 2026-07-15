# edge-allow: open, shutil.copy, shutil.move
from os import remove
from shutil import copyfileobj
from gzip import open as gz_open
from shared.models.log import Config


class Gzip:
    """Tiny Class that can be called with instantiated values to help log write class"""

    def __init__(self, config: Config):
        self.instance_uuid = config.UUID4
        self.now_str = config.Now().strftime("%Y%m%d-%H%M%S")

    def namer(self, name: str) -> str:
        # inject the uuid into the rotated filename
        return f"{name}.{self.now_str}.{self.instance_uuid()}.gz"

    def rotator(self, src: str, dst: str) -> None:
        with open(src, "rb") as f_in, gz_open(dst, "wb") as f_out:
            copyfileobj(f_in, f_out)
        remove(src)
