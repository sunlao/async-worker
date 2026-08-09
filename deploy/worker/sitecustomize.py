from os import getenv

if getenv("ENV", "NOT_CI") == "ci":
    import coverage
    coverage.process_startup()
