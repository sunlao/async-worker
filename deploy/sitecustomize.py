from os import getenv

if getenv("ENV", "NOTCI") == "ci":
    import coverage
    coverage.process_startup()
