"""Ensembl REST API client."""

from app.clients.base_client import BaseClient
from app.config import settings


class EnsemblClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.ENSEMBL_BASE_URL)

    async def get_sequence(self, stable_id: str, seq_type: str = "cdna") -> dict:
        response = await self.get(
            f"/sequence/id/{stable_id}",
            params={"type": seq_type, "content-type": "application/json"},
        )
        return response.json()

    async def lookup_symbol(self, species: str, symbol: str) -> dict:
        response = await self.get(
            f"/lookup/symbol/{species}/{symbol}",
            params={"content-type": "application/json"},
        )
        return response.json()

    async def get_xrefs(self, stable_id: str) -> list:
        response = await self.get(
            f"/xrefs/id/{stable_id}",
            params={"content-type": "application/json"},
        )
        return response.json()


ensembl_client = EnsemblClient()
