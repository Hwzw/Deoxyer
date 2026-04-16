"""JASPAR REST API client for transcription factor binding motifs."""

from app.clients.base_client import BaseClient
from app.config import settings


class JASPARClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.JASPAR_BASE_URL)

    async def search_profiles(
        self, query: str, tax_group: str | None = None, limit: int = 20
    ) -> dict:
        params = {"search": query, "page_size": limit, "format": "json"}
        if tax_group:
            params["tax_group"] = tax_group
        response = await self.get("/matrix/", params=params)
        return response.json()

    async def get_matrix(self, matrix_id: str) -> dict:
        response = await self.get(f"/matrix/{matrix_id}/", params={"format": "json"})
        return response.json()


jaspar_client = JASPARClient()
