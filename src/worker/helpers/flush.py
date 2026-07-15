# pylint: disable=import-outside-toplevel
# pylint: disable=duplicate-code


def save(ctx):
    """Exists to support code coverage
    - execute in env ci only"""
    log = ctx["config_log"]
    env = log.Environment
    if env == "ci":
        # only import in ci env
        from coverage import Coverage

        cov = Coverage.current()
        if cov:
            cov.save()
