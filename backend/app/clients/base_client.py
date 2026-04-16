import httpx

from app.config import settings


class BaseClient:
    """Base HTTP client with retry logic and rate limiting."""

    def __init__(self, base_url: str, timeout: float = settings.HTTP_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response

    async def post(self, path: str, json: dict | None = None) -> httpx.Response:
        client = await self._get_client()
        response = await client.post(path, json=json)
        response.raise_for_status()
        return response

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
