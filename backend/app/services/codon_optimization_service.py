"""Core codon optimization engine.

Uses DNAchisel for constraint-based optimization and python-codon-tables
for organism-specific codon usage frequencies.
"""

import copy

from dnachisel import (
    AvoidPattern,
    CodonOptimize,
    DnaOptimizationProblem,
    EnforceGCContent,
    EnforceTranslation,
)

from app.config import settings
from app.services.organism_service import get_codon_table
from app.utils.codon_tables import calculate_cai
from app.utils.sequence import gc_content, reverse_translate

STOP_CODONS = ["TAA", "TAG", "TGA"]


def _select_stop_codons(codon_table: dict) -> str:
    """Select 2-3 tandem stop codons for reliable translation termination.

    Uses the organism's codon usage to pick the preferred stop codon first,
    then appends a different stop codon for read-through protection.
    """
    # Get stop codon frequencies from the codon table (keyed under '*')
    stop_freqs = {}
    if "*" in codon_table:
        stop_freqs = codon_table["*"]

    # Sort stop codons by usage frequency (most preferred first)
    ranked = sorted(STOP_CODONS, key=lambda c: stop_freqs.get(c, 0), reverse=True)

    # Use preferred stop + a different backup + a third for safety
    return ranked[0] + ranked[1] + ranked[2]


def optimize_sequence(
    protein_sequence: str,
    organism_tax_id: int,
    strategy: str = "frequency",
    avoid_restriction_sites: list[str] | None = None,
    target_gc_min: float | None = None,
    target_gc_max: float | None = None,
    avoid_repeats: bool = True,
) -> dict:
    """Optimize a protein sequence for expression in the target organism.

    Returns dict with optimized_sequence, cai_before, cai_after, gc_content.
    """
    codon_table = get_codon_table(organism_tax_id)

    # Step 1: Reverse translate protein to initial DNA sequence
    initial_dna = reverse_translate(protein_sequence, codon_table.table)

    # Step 2: Set up DNAchisel optimization problem
    constraints = [
        EnforceTranslation(),
    ]
    objectives = [
        CodonOptimize(species=None, codon_usage_table=copy.deepcopy(codon_table.table)),
    ]

    if target_gc_min is not None and target_gc_max is not None:
        constraints.append(
            EnforceGCContent(mini=target_gc_min, maxi=target_gc_max, window=settings.GC_CONTENT_WINDOW)
        )

    if avoid_restriction_sites:
        for site in avoid_restriction_sites:
            constraints.append(AvoidPattern(site))

    if avoid_repeats:
        constraints.append(AvoidPattern(settings.REPEAT_AVOIDANCE_PATTERN))

    problem = DnaOptimizationProblem(
        sequence=initial_dna,
        constraints=constraints,
        objectives=objectives,
    )

    # Step 3: Resolve constraints then optimize
    problem.resolve_constraints()
    problem.optimize()

    optimized_dna = problem.sequence

    # Step 4: Append tandem stop codons for reliable termination
    # Use two different stop codons to guard against read-through
    stop_codons = _select_stop_codons(codon_table.table)
    optimized_dna += stop_codons

    # Step 5: Calculate metrics
    gc_before = gc_content(initial_dna)
    gc_after = gc_content(optimized_dna)

    cai_before = round(calculate_cai(initial_dna, codon_table.table), 4)
    cai_after = round(calculate_cai(optimized_dna, codon_table.table), 4)

    return {
        "initial_sequence": initial_dna,
        "optimized_sequence": optimized_dna,
        "gc_content_before": gc_before,
        "gc_content_after": gc_after,
        "cai_before": cai_before,
        "cai_after": cai_after,
    }
