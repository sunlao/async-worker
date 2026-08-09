def info():
    name = "AsyncWorker"
    description = """A pythonic template repo for API based services that needs
    async workers for non blocking FIFO jobs. """
    return {"name": name, "description": description}


def tags():
    return [info()]
