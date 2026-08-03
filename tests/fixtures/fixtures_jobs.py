from pytest import fixture
from worker_old.controller.movement import Movement
from shared.models.constants import JobTypes
from shared.models.worker import EnqueueRequest


@fixture
def controller_movement():
    return Movement


@fixture
def job_100(reader):
    """Test Job that sleeps for 3 seconds"""
    return EnqueueRequest(
        JobType=JobTypes.MOVEMENT, Job=reader.config(100), EnqueueGate=False
    )
