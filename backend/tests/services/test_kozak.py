"""Tests for Kozak sequence generation."""

from app.services.kozak_service import generate_kozak


def test_human_kozak():
    result = generate_kozak(organism_tax_id=9606)
    assert result["consensus"] == "gccRccATGG"
    assert "ATG" in result["sequence"].upper()


def test_yeast_kozak():
    result = generate_kozak(organism_tax_id=4932)
    assert "ATG" in result["sequence"]
    assert result["organism_tax_id"] == 4932


def test_unknown_organism_defaults_to_vertebrate():
    result = generate_kozak(organism_tax_id=99999)
    assert result["consensus"] == "GCCACCATGG"
