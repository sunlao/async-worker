class ProcessExecutionFailure(Exception):
    def __init__(self, p_process, p_code, p_output):
        super().__init__(
            f"{p_process} execution != 0: result code: {p_code} with "
            f"output:\n {p_output}"
        )


class PyLintScoreFailure(Exception):
    def __init__(self, p_score):
        super().__init__(f"pylint score != 10.0: score: {p_score}")
