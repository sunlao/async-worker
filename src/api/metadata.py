def info():
    name = "AsyncServ"
    description = """A pythonic template repo for API based services that needs
    async workers for non blocking jobs. """
    return {"name": name, "description": description}


def tags():
    return [
        info(),
    ]
