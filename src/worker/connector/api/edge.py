class Edge:
    """Connector for the platform-owned HTTP client passed from the edge."""

    def __init__(self, context):
        self.client = context["http_client"]

    async def get(self, url: str):
        response = await self.client.get(url)
        response.raise_for_status()
        return response
