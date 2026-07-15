from shared.log.helpers.clean import sanitize_str
from shared.models.log import (
    Core,
    Config,
    CoreError,
    Event,
    EventError,
)


class Serializer:
    """Serialize and transform log DTO's to a flat santized dict for the log writer"""

    def __init__(self, config: Config):
        self.service = config.Service
        self.env = config.Environment
        self.log_level = config.Level

    @staticmethod
    def flaten_core(dto: Core) -> dict:
        model = dto.model_copy(update={"Message": sanitize_str(dto.Message)})
        flat = model.model_dump(mode="json")
        return flat

    @staticmethod
    def flaten_core_error(dto: CoreError) -> dict:
        core = dto.Core.model_copy(update={"Message": sanitize_str(dto.Core.Message)})
        flat = core.model_dump(mode="json")
        error = dto.Error.model_copy(
            update={"Message": sanitize_str(dto.Error.ExceptionMessage)}
        )
        flat.update(error.model_dump(mode="json"))
        return flat

    @staticmethod
    def flaten_event(dto: Event) -> dict:
        copy = dto.Core.model_copy(update={"Message": sanitize_str(dto.Core.Message)})
        flat = copy.model_dump(mode="json")
        flat.update(dto.Event.model_dump(mode="json"))
        return flat

    @staticmethod
    def flaten_event_error(dto: EventError) -> dict:
        copy = dto.Core.model_copy(update={"Message": sanitize_str(dto.Core.Message)})
        flat = copy.model_dump(mode="json")
        flat.update(dto.Event.model_dump(mode="json"))
        error = dto.Error.model_copy(
            update={"Message": sanitize_str(dto.Error.ExceptionMessage)}
        )
        flat.update(error.model_dump(mode="json"))
        return flat
