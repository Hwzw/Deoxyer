"""Tests for codon optimization endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch


@patch("app.dependencies.get_db")
@patch("app.services.codon_optimization_service.optimize_sequence")
def test_optimize_codons(mock_optimize, mock_db, client):
    mock_optimize.return_value = {
        "initial_sequence": "ATGATGATG",
        "optimized_sequence": "ATGATGATG",
        "gc_content_before": 0.33,
        "gc_content_after": 0.33,
        "cai_before": 0.7,
        "cai_after": 0.85,
    }

    # Mock database session for job persistence
    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = "12345678-1234-1234-1234-123456789012"
    mock_job.status = "completed"
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_db.return_value = mock_session

    response = client.post(
        "/api/optimization/optimize",
        json={
            "sequence": "MMM",
            "organism_tax_id": 562,
            "strategy": "frequency",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["optimized_sequence"] == "ATGATGATG"
    assert data["cai_before"] == 0.7
    assert data["cai_after"] == 0.85
    assert "job_id" in data
    assert data["status"] == "completed"


@patch("app.dependencies.get_db")
@patch("app.services.codon_optimization_service.optimize_sequence")
def test_optimize_failure(mock_optimize, mock_db, client):
    mock_optimize.side_effect = Exception("DNAchisel error")

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_db.return_value = mock_session

    response = client.post(
        "/api/optimization/optimize",
        json={"sequence": "XXX", "organism_tax_id": 562},
    )
    assert response.status_code == 500
    assert "Optimization failed" in response.json()["detail"]
