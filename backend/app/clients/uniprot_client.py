"""UniProt REST API v2 client."""

from app.clients.base_client import BaseClient
from app.config import settings


class UniProtClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.UNIPROT_BASE_URL)

    async def search_proteins(
        self, query: str, organism: str | None = None, limit: int = 20
    ) -> dict:
        search_query = query
        if organism:
            search_query = f"{query} AND organism_name:{organism}"
        response = await self.get(
            "/uniprotkb/search",
            params={"query": search_query, "size": limit, "format": "json"},
        )
        return response.json()

    async def get_entry(self, accession: str) -> dict:
        response = await self.get(f"/uniprotkb/{accession}.json")
        return response.json()

    async def get_fasta(self, accession: str) -> str:
        client = await self._get_client()
        response = await client.get(
            f"/uniprotkb/{accession}.fasta",
            headers={"Accept": "text/plain"},
        )
        response.raise_for_status()
        return response.text


uniprot_client = UniProtClient()
