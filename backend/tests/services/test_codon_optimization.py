"""Tests for codon optimization service logic."""

from unittest.mock import MagicMock, patch

from app.services.codon_optimization_service import optimize_sequence


@patch("app.services.codon_optimization_service.DnaOptimizationProblem")
@patch("app.services.codon_optimization_service.get_codon_table")
def test_optimize_returns_cai(mock_codon_table, mock_problem_cls):
    """Verify that optimize_sequence returns non-None CAI values."""
    mock_codon_table.return_value = MagicMock(
        table={
            "M": {"ATG": 1.0},
            "A": {"GCG": 0.36, "GCC": 0.27, "GCA": 0.21, "GCT": 0.16},
        }
    )

    mock_problem = MagicMock()
    mock_problem.sequence = "ATGGCG"
    mock_problem_cls.return_value = mock_problem

    result = optimize_sequence(
        protein_sequence="MA",
        organism_tax_id=562,
    )

    assert result["cai_before"] is not None
    assert result["cai_after"] is not None
    assert isinstance(result["cai_before"], float)
    assert isinstance(result["cai_after"], float)
    assert 0.0 <= result["cai_before"] <= 1.0
    assert 0.0 <= result["cai_after"] <= 1.0


@patch("app.services.codon_optimization_service.DnaOptimizationProblem")
@patch("app.services.codon_optimization_service.get_codon_table")
def test_optimize_gc_content_calculated(mock_codon_table, mock_problem_cls):
    """Verify GC content is calculated before and after optimization."""
    mock_codon_table.return_value = MagicMock(
        table={
            "M": {"ATG": 1.0},
            "G": {"GGC": 0.4, "GGT": 0.3, "GGA": 0.2, "GGG": 0.1},
        }
    )

    mock_problem = MagicMock()
    mock_problem.sequence = "ATGGGC"
    mock_problem_cls.return_value = mock_problem

    result = optimize_sequence(protein_sequence="MG", organism_tax_id=562)
    assert result["gc_content_before"] is not None
    assert result["gc_content_after"] is not None
    assert isinstance(result["gc_content_before"], float)


@patch("app.services.codon_optimization_service.DnaOptimizationProblem")
@patch("app.services.codon_optimization_service.get_codon_table")
def test_optimize_returns_sequences(mock_codon_table, mock_problem_cls):
    """Verify both initial and optimized sequences are returned."""
    mock_codon_table.return_value = MagicMock(
        table={
            "M": {"ATG": 1.0},
            "K": {"AAG": 0.6, "AAA": 0.4},
        }
    )

    mock_problem = MagicMock()
    mock_problem.sequence = "ATGAAG"
    mock_problem_cls.return_value = mock_problem

    result = optimize_sequence(protein_sequence="MK", organism_tax_id=562)
    assert "initial_sequence" in result
    assert "optimized_sequence" in result
    assert len(result["initial_sequence"]) == 6
    assert len(result["optimized_sequence"]) == 6
