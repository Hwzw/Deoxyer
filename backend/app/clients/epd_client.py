"""EPD (Eukaryotic Promoter Database) client."""

from app.clients.base_client import BaseClient
from app.config import settings


class EPDClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.EPD_BASE_URL)

    async def search_promoters(
        self, organism: str, gene: str | None = None, limit: int = 20
    ) -> dict:
        params = {"organism": organism, "limit": limit}
        if gene:
            params["gene"] = gene
        response = await self.get("/search", params=params)
        return response.json()

    async def get_promoter_sequence(self, promoter_id: str) -> dict:
        response = await self.get(f"/promoter/{promoter_id}")
        return response.json()


epd_client = EPDClient()
