"""CoCoPUTs (Codon and Codon Pair Usage Tables) client.

Fetches organism-specific codon usage data from NCBI's CoCoPUTs database.
"""

from app.clients.base_client import BaseClient
from app.config import settings


class CoCoPUTsClient(BaseClient):
    def __init__(self):
        super().__init__(base_url=settings.COCOPUTS_BASE_URL, timeout=settings.COCOPUTS_TIMEOUT)

    async def get_codon_usage(self, tax_id: int) -> dict:
        """Fetch codon usage table for an organism by taxonomy ID."""
        response = await self.get(
            "",
            params={"cmd": "codon_usage", "id": str(tax_id), "format": "json"},
        )
        return response.json()


cocoputs_client = CoCoPUTsClient()
