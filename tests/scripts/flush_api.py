from sys import stderr
from urllib import request
from json import loads


def poke(service: str, port: int):
    """Post to flush api to make code coverage work
    Only used for CI pipelines"""
    url = f"http://awork-{service}:{port}/api/v1/flush"
    try:
        req = request.Request(url, method="POST")
        with request.urlopen(req, timeout=5) as resp:
            body = resp.read()  # bytes
            doc = loads(body.decode())  # dict
        print(f"doc : {doc}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print("flush failed:", url, e, file=stderr)


poke("api", 80)