"""Tests for gene search and detail endpoints."""

from unittest.mock import AsyncMock, patch

MOCK_ESEARCH_RESULT = {"IdList": ["7157"]}

MOCK_ESUMMARY_GENE = {
    "DocumentSummarySet": {
        "DocumentSummary": [
            {
                "Name": "TP53",
                "Description": "tumor protein p53",
                "Summary": "This gene encodes a tumor suppressor protein.",
                "Organism": {"ScientificName": "Homo sapiens", "TaxID": "9606"},
                "Chromosome": "17",
                "MapLocation": "17p13.1",
                "OtherAliases": "BCC7, LFS1, P53",
            }
        ]
    }
}


@patch("app.services.gene_service.ncbi_client.esummary", new_callable=AsyncMock)
@patch("app.services.gene_service.ncbi_client.search_genes", new_callable=AsyncMock)
def test_gene_search(mock_search, mock_summary, client):
    mock_search.return_value = MOCK_ESEARCH_RESULT
    mock_summary.return_value = MOCK_ESUMMARY_GENE

    response = client.get("/api/genes/search?q=TP53&organism=human")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "TP53"
    assert data[0]["organism"] == "Homo sapiens"


@patch("app.dependencies.get_cache")
@patch("app.services.gene_service.ncbi_client.esummary", new_callable=AsyncMock)
def test_get_gene_detail(mock_summary, mock_cache, client):
    mock_cache.return_value = AsyncMock(get_cached=AsyncMock(return_value=None), set_cached=AsyncMock())
    mock_summary.return_value = MOCK_ESUMMARY_GENE

    response = client.get("/api/genes/7157")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "TP53"
    assert data["tax_id"] == 9606
    assert "BCC7" in data["aliases"]
    assert data["chromosome"] == "17"


@patch("app.dependencies.get_cache")
@patch("app.services.gene_service.ncbi_client.esummary", new_callable=AsyncMock)
def test_get_gene_not_found(mock_summary, mock_cache, client):
    mock_cache.return_value = AsyncMock(get_cached=AsyncMock(return_value=None))
    mock_summary.return_value = {"DocumentSummarySet": {"DocumentSummary": []}}

    response = client.get("/api/genes/999999999")
    assert response.status_code == 404
