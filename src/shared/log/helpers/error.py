# edge-allow: pathlib
from pathlib import Path
from traceback import FrameSummary, extract_tb
from shared.models.constants import PathParts
from shared.models.log import TraceBackEvent, LastPartTB, RelPathInput


class Error:
    """Supporting Logging module to build traceback information from errors"""

    @staticmethod
    def _is_part(tb_sum: FrameSummary, path_part: PathParts) -> bool:
        parts = Path(tb_sum.filename).parts
        return path_part in parts

    @staticmethod
    def _rel_part_path(dto: RelPathInput) -> str:
        parts = Path(dto.TBPath).parts
        try:
            idx = parts.index(dto.PathPart)
        except ValueError:
            return dto.TBPath
        return "/".join(parts[(idx):])

    def _last_part_tb(
        self, tb_sum_all: list[FrameSummary], path_part: str
    ) -> LastPartTB:
        last = next(
            (tb for tb in reversed(tb_sum_all) if self._is_part(tb, path_part)),
            None,
        )
        if last is None:
            return LastPartTB(Path="<unknown>", LineNo=0, FunctionName="<unknown>")
        return LastPartTB(
            Path=last.filename, LineNo=last.lineno, FunctionName=last.name
        )

    def trace_back_nfo(
        self, exc_class: BaseException, path_part: PathParts = PathParts.SRC
    ) -> TraceBackEvent:
        """Build a structured DTO for logging from traceback information from an
        exception class output object"""
        tb_all = extract_tb(exc_class.__traceback__)
        last_tb = self._last_part_tb(tb_all, path_part)
        exc = f"{exc_class.__class__.__module__}.{exc_class.__class__.__qualname__}"
        last_5_tb = [
            (
                self._rel_part_path(
                    RelPathInput(TBPath=tb.filename, PathPart=path_part)
                ),
                tb.lineno,
                tb.name,
            )
            for tb in tb_all[-5:]
        ]
        rp_input = RelPathInput(TBPath=last_tb.Path, PathPart=path_part)
        tb_file = self._rel_part_path(rp_input)
        return TraceBackEvent(
            Exception=exc,
            ExceptionMessage=str(exc_class),
            LastTBFile=tb_file,
            LastTBLineNo=last_tb.LineNo,
            LastTBFunction=last_tb.FunctionName,
            Last5TB=last_5_tb,
            TBCount=len(tb_all),
        )
