"""Restriction enzyme digest for assembled constructs.

Wraps BioPython's Restriction module to produce cut positions, fragments,
and annotation intersections for a given sequence + enzyme panel.
"""

from __future__ import annotations

from fastapi import HTTPException

from Bio.Restriction import AllEnzymes, RestrictionBatch
from Bio.Seq import Seq


_ENZYME_BY_LOWER = {str(e).lower(): str(e) for e in AllEnzymes}


def resolve_enzymes(names: list[str]) -> list[str]:
    """Look up enzyme names case-insensitively. Raise 400 on unknowns."""
    resolved: list[str] = []
    unknown: list[str] = []
    for name in names:
        canonical = _ENZYME_BY_LOWER.get(name.strip().lower())
        if canonical is None:
            unknown.append(name)
        else:
            resolved.append(canonical)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown enzyme(s): {', '.join(unknown)}",
        )
    # De-duplicate while preserving first-seen order
    seen: set[str] = set()
    deduped = []
    for n in resolved:
        if n not in seen:
            seen.add(n)
            deduped.append(n)
    return deduped


def digest(
    sequence: str,
    enzyme_names: list[str],
    annotations: list[dict] | None = None,
) -> dict:
    """Perform a restriction digest on a linear sequence.

    Returns a dict with:
      - sequence_length
      - enzymes: per-enzyme info (site, 0-based cut positions, overhang type,
        list of feature labels each cut falls within)
      - fragments: linear fragments produced by combined cuts (0-based half-open)
      - warnings: notable observations (e.g. enzyme did not cut)
    """
    if not sequence:
        raise HTTPException(status_code=400, detail="Sequence is empty; nothing to digest.")

    canonical = resolve_enzymes(enzyme_names)
    seq = Seq(sequence)
    batch = RestrictionBatch(canonical)
    hits = batch.search(seq, linear=True)  # {Enzyme: [1-based cut positions]}

    annotations = annotations or []
    warnings: list[str] = []

    enzyme_infos = []
    all_cuts_0b: list[int] = []
    for enzyme_name in canonical:
        enzyme_obj = next(e for e in hits if str(e) == enzyme_name)
        positions_1b = hits[enzyme_obj]
        # BioPython reports 1-based position of the first base AFTER the cut.
        # Convert to 0-based so callers match our annotation coordinate system.
        positions_0b = [p - 1 for p in positions_1b]
        all_cuts_0b.extend(positions_0b)

        if not positions_0b:
            warnings.append(f"{enzyme_name} does not cut this sequence.")

        feature_hits = _features_at_cuts(positions_0b, annotations)

        enzyme_infos.append({
            "name": enzyme_name,
            "site": str(enzyme_obj.site),
            "cut_positions": positions_0b,
            "cut_count": len(positions_0b),
            "overhang": _overhang_label(enzyme_obj),
            "feature_hits": feature_hits,
        })

    fragments = _fragments_from_cuts(sequence, all_cuts_0b)

    return {
        "sequence_length": len(sequence),
        "full_sequence": sequence,
        "enzymes": enzyme_infos,
        "fragments": fragments,
        "annotations": annotations,
        "warnings": warnings,
    }


def _overhang_label(enzyme) -> str:
    if enzyme.is_blunt():
        return "blunt"
    if enzyme.is_5overhang():
        return "5' overhang"
    if enzyme.is_3overhang():
        return "3' overhang"
    return "unknown"


def _features_at_cuts(cuts_0b: list[int], annotations: list[dict]) -> list[str]:
    labels: list[str] = []
    for cut in cuts_0b:
        for annot in annotations:
            if annot["start"] <= cut < annot["end"] and annot["label"] not in labels:
                labels.append(annot["label"])
    return labels


def _fragments_from_cuts(sequence: str, cuts_0b: list[int]) -> list[dict]:
    if not cuts_0b:
        return [{
            "index": 0,
            "start": 0,
            "end": len(sequence),
            "length": len(sequence),
            "sequence": _preview(sequence),
        }]
    boundaries = sorted(set(cuts_0b))
    edges = [0] + boundaries + [len(sequence)]
    fragments = []
    for i in range(len(edges) - 1):
        start, end = edges[i], edges[i + 1]
        sub = sequence[start:end]
        fragments.append({
            "index": i,
            "start": start,
            "end": end,
            "length": end - start,
            "sequence": _preview(sub),
        })
    return fragments


def _preview(sequence: str, max_len: int = 60) -> str:
    if len(sequence) <= max_len:
        return sequence
    head = sequence[: max_len // 2]
    tail = sequence[-max_len // 2 :]
    return f"{head}...{tail}"
