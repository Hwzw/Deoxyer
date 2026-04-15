"""Tests for codon optimization endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.dependencies import get_db
from app.main import app

_TEST_JOB_ID = uuid.UUID("12345678-1234-1234-1234-123456789012")


def _mock_db_session():
    mock_session = AsyncMock()

    def _add_sets_id(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = _TEST_JOB_ID

    mock_session.add = MagicMock(side_effect=_add_sets_id)
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


@patch("app.services.codon_optimization_service.optimize_sequence")
def test_optimize_codons(mock_optimize, client):
    mock_optimize.return_value = {
        "initial_sequence": "ATGATGATG",
        "optimized_sequence": "ATGATGATG",
        "gc_content_before": 0.33,
        "gc_content_after": 0.33,
        "cai_before": 0.7,
        "cai_after": 0.85,
    }

    mock_session = _mock_db_session()
    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        response = client.post(
            "/api/optimization/optimize",
            json={
                "sequence": "MMM",
                "organism_tax_id": 562,
                "strategy": "frequency",
            },
            headers={"X-Session-ID": "12345678-1234-1234-1234-123456789012"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert data["optimized_sequence"] == "ATGATGATG"
    assert data["cai_before"] == 0.7
    assert data["cai_after"] == 0.85
    assert "job_id" in data
    assert data["status"] == "completed"


@patch("app.services.codon_optimization_service.optimize_sequence")
def test_optimize_failure(mock_optimize, client):
    mock_optimize.side_effect = Exception("DNAchisel error")

    mock_session = _mock_db_session()
    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        response = client.post(
            "/api/optimization/optimize",
            json={"sequence": "XXX", "organism_tax_id": 562},
            headers={"X-Session-ID": "12345678-1234-1234-1234-123456789012"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 500
    assert "Optimization failed" in response.json()["detail"]
