from collections.abc import Hashable
from typing import Any


class Registry:
    """Register Job Types with jobs in support of creating a client for the queue"""
    def __init__(self) -> None:
        self._registry: dict[Hashable, Any] = {}

    def put(self, job_type: Hashable, job_name: Any) -> None:
        if job_type in self._registry:
            raise ValueError(f"Job Type already registered: {job_type}")

        self._registry[job_type] = job_name

    def get(self, job_type: Hashable) -> Any:
        try:
            return self._registry[job_type]
        except KeyError as error:
            raise KeyError(f"Task not registered: {job_type}") from error
