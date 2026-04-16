"""Terminator search and selection service.

Loads terminator data from CSV for transcription terminator lookup.
"""

import csv
from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.schemas.regulatory import TerminatorInfo, TerminatorSearchResult

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Loaded once at first access
_TERMINATOR_DATA: list[TerminatorInfo] = []


def _load_terminators() -> list[TerminatorInfo]:
    global _TERMINATOR_DATA
    if _TERMINATOR_DATA:
        return _TERMINATOR_DATA

    csv_path = DATA_DIR / "terminators.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name") or "").strip()
            organism = (row.get("Organism") or "").strip()
            if not name or not organism:
                continue

            sequence = (row.get("sequence") or "").strip().replace(" ", "")
            mechanism = (row.get("Mechanism") or "").strip()
            score = (row.get("Efficiency_Score") or "").strip()
            size = (row.get("Size") or "").strip()
            usable_in = (row.get("Usable_In") or "").strip()
            generalizable_raw = (row.get("Generalizable") or "").strip().lower()
            commonly_paired_with = (row.get("Commonly_Paired_With") or "").strip()
            notes = (row.get("Notes") or "").strip()

            # Map efficiency score to rating
            efficiency = None
            if score:
                try:
                    s = int(score)
                    if s >= settings.TERMINATOR_HIGH_THRESHOLD:
                        efficiency = "high"
                    elif s >= settings.TERMINATOR_MODERATE_THRESHOLD:
                        efficiency = "moderate"
                    else:
                        efficiency = "low"
                except ValueError:
                    pass

            generalizable = generalizable_raw == "yes" if generalizable_raw in ("yes", "no") else None

            # Generate a stable ID from the name
            terminator_id = "csv_" + name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").replace("-", "_")

            _TERMINATOR_DATA.append(TerminatorInfo(
                id=terminator_id,
                name=name,
                organism=organism,
                sequence=sequence,
                length=len(sequence),
                mechanism=mechanism or None,
                efficiency=efficiency,
                size=size or None,
                usable_in=usable_in or None,
                generalizable=generalizable,
                commonly_paired_with=commonly_paired_with or None,
                notes=notes or None,
            ))

    return _TERMINATOR_DATA


# Map common tax IDs to organism names used in the CSV
_TAX_ID_TO_ORGANISM = {
    562: "E. coli",
    9606: "Human",
    10090: "Murine",
    4932: "S. cerevisiae",
    3702: "Arabidopsis",
    4577: "Zea mays",
    7227: "Drosophila",
    1423: "Bacillus subtilis",
    1613: "Lactococcus lactis",
    4081: "Pichia pastoris",
    5141: "Aspergillus nidulans",
    176275: "Agrobacterium tumefaciens",
    3888: "Pisum sativum",
}


def _match_organism(terminator: TerminatorInfo, query: str) -> bool:
    """Check if a terminator matches an organism search query."""
    q = query.strip()
    if q.isdigit():
        q = _TAX_ID_TO_ORGANISM.get(int(q), q)
    q = q.lower()
    fields = [
        terminator.organism.lower(),
        terminator.name.lower(),
        (terminator.usable_in or "").lower(),
        (terminator.notes or "").lower(),
    ]
    return any(q in f for f in fields)


async def search_terminators(
    organism: str, limit: int = 20
) -> TerminatorSearchResult:
    """Search for terminators by organism."""
    terminators: list[TerminatorInfo] = []

    all_terminators = _load_terminators()
    for t in all_terminators:
        if _match_organism(t, organism):
            terminators.append(t)

    message = None
    if not terminators:
        if organism.strip().isdigit() and int(organism) not in _TAX_ID_TO_ORGANISM:
            message = f"Tax ID {organism} is not in the supported terminator list. Try searching by organism name."
        else:
            message = f"No terminators found for '{organism}'. Try a broader search term or different organism."

    return TerminatorSearchResult(terminators=terminators[:limit], total=len(terminators), message=message)


async def get_terminator(terminator_id: str) -> TerminatorInfo:
    """Fetch a specific terminator by ID."""
    all_terminators = _load_terminators()
    for t in all_terminators:
        if t.id == terminator_id:
            return t

    raise HTTPException(
        status_code=404, detail=f"Terminator {terminator_id} not found"
    )
