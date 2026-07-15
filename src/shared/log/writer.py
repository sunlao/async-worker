from sys import stdout
import logging
from logging.handlers import TimedRotatingFileHandler
from json import dumps
from shared.log.serializer import Serializer
from shared.log.helpers.gzip import Gzip
from shared.models.log import Core, Event, Config


class Writer:
    """Write logs by log type"""

    def __init__(self, config: Config):
        self.gzip = Gzip(config)
        self.root = logging.getLogger(config.Service)
        # Starlette/Uvicorn insist on lower case
        self.log_level = config.Level.upper()
        self.root.setLevel(self.log_level)
        self.root.handlers = []
        self.root.addHandler(logging.StreamHandler(stream=stdout))
        self.level_map = logging.getLevelNamesMapping()
        if config.LogToFile:
            self._file_handler(config)
        self.config = config

    def _file_handler(self, dto: Config) -> None:
        handler = TimedRotatingFileHandler(
            dto.LogDirectory,
            when="midnight",
            interval=1,
            backupCount=dto.BackUpCount,
            encoding="utf-8",
            utc=True,
        )
        handler.namer = self.gzip.namer
        handler.rotator = self.gzip.rotator
        handler.setLevel(self.log_level)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.root.addHandler(handler)

    def _write(self, p_input: dict) -> None:
        json = dumps(p_input, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
        init_lvl = getattr(logging, self.log_level, logging.INFO)
        # Starlette/Uvicorn insist on lower case
        event_lvl = self.level_map[p_input["InputLevel"].upper()]
        if event_lvl >= init_lvl:
            self.root.log(event_lvl, json)

    def write_core(self, dto: Core) -> None:
        """Write log core logs"""
        log = Serializer(self.config).flaten_core(dto=dto)
        self._write(log)

    def write_core_error(self, dto: Core) -> None:
        """Write log core error logs"""
        log = Serializer(self.config).flaten_core_error(dto=dto)
        self._write(log)

    def write_event(self, dto: Event) -> None:
        """Write log events"""
        log = Serializer(self.config).flaten_event(dto=dto)
        self._write(log)

    def write_event_error(self, dto: Event) -> None:
        """ "Write log event errors"""
        log = Serializer(self.config).flaten_event_error(dto=dto)
        self._write(log)
