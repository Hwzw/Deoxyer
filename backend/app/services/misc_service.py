"""Miscellaneous sequence search and retrieval service.

Loads curated protein/DNA elements (tags, linkers, origins, selection markers,
insulators, etc.) from CSV.
"""

import csv
import re
from pathlib import Path

from fastapi import HTTPException

from app.schemas.misc import MiscSearchResult, MiscSequenceInfo

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_MISC_DATA: list[MiscSequenceInfo] = []


def _slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _clean_sequence(seq: str, sequence_type: str) -> str:
    s = re.sub(r"\s+", "", seq)
    if sequence_type == "dna":
        s = s.replace("-", "").upper()
    return s


def _load_misc() -> list[MiscSequenceInfo]:
    global _MISC_DATA
    if _MISC_DATA:
        return _MISC_DATA

    csv_path = DATA_DIR / "misc_sequences.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name") or "").strip()
            if not name:
                continue
            category = (row.get("Category") or "").strip() or None
            subtype = (row.get("Type") or "").strip() or None
            seq_type_raw = (row.get("Sequence Type") or "").strip().lower()
            sequence_type = "protein" if seq_type_raw == "protein" else "dna"
            sequence = _clean_sequence(row.get("Sequence") or "", sequence_type)
            notes = (row.get("Notes") or "").strip() or None
            _MISC_DATA.append(
                MiscSequenceInfo(
                    id="misc_" + _slugify(name),
                    name=name,
                    category=category,
                    subtype=subtype,
                    sequence_type=sequence_type,
                    sequence=sequence,
                    length=len(sequence),
                    notes=notes,
                )
            )

    return _MISC_DATA


async def search_misc(
    query: str | None = None,
    sequence_type: str | None = None,
    limit: int = 50,
) -> MiscSearchResult:
    """Free-text search across name/category/subtype/notes, optionally filtered by sequence_type."""
    all_misc = _load_misc()
    q = (query or "").lower().strip()
    st = sequence_type.lower().strip() if sequence_type else None
    if st and st not in ("protein", "dna"):
        st = None

    matches: list[MiscSequenceInfo] = []
    for m in all_misc:
        if st and m.sequence_type != st:
            continue
        if q:
            hay = " ".join(
                [
                    m.name.lower(),
                    (m.category or "").lower(),
                    (m.subtype or "").lower(),
                    (m.notes or "").lower(),
                ]
            )
            if q not in hay:
                continue
        matches.append(m)

    message = None
    if not matches:
        suffix = f" for '{query}'" if query else ""
        message = f"No misc sequences found{suffix}."

    return MiscSearchResult(items=matches[:limit], total=len(matches), message=message)


async def get_misc(misc_id: str) -> MiscSequenceInfo:
    """Fetch a specific misc sequence by id or name (case-insensitive)."""
    target_slug = "misc_" + _slugify(misc_id)
    for m in _load_misc():
        if m.id == misc_id or m.id == target_slug or m.name.lower() == misc_id.lower():
            return m
    raise HTTPException(status_code=404, detail=f"Misc sequence '{misc_id}' not found")
