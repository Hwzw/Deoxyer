"""Construct assembly service.

Takes ordered genetic elements and assembles them into a full construct sequence.
Validates junctions and reading frames.
"""

from app.schemas.construct import ConstructElementSchema


def assemble_construct(elements: list[ConstructElementSchema]) -> dict:
    """Assemble ordered elements into a complete construct sequence.

    Returns dict with full_sequence, length, annotations (element positions).
    """
    sorted_elements = sorted(elements, key=lambda e: e.position)

    full_sequence = ""
    annotations = []
    current_pos = 0
    prev_element = None

    for element in sorted_elements:
        seq = element.sequence

        # Handle Kozak→CDS junction: the Kozak includes ATG (start codon)
        # plus optional context nucleotides after it. Trim the Kozak back
        # to just before the ATG so the ATG belongs to the CDS annotation
        # (preserving correct reading frame for codon display).
        if element.element_type == "cds" and prev_element and prev_element.element_type == "kozak":
            kozak_seq = prev_element.sequence.upper()
            atg_idx = kozak_seq.rfind("ATG")
            if atg_idx >= 0:
                # Remove everything from ATG onward from the kozak
                chars_from_atg = len(kozak_seq) - atg_idx
                full_sequence = full_sequence[:-chars_from_atg]
                current_pos -= chars_from_atg
                annotations[-1]["end"] -= chars_from_atg
                annotations[-1]["length"] -= chars_from_atg

            # Keep the CDS sequence intact (including its ATG)

        start = current_pos
        full_sequence += seq
        end = current_pos + len(seq)
        annotations.append({
            "type": element.element_type,
            "label": element.label,
            "start": start,
            "end": end,
            "length": len(seq),
        })
        current_pos = end
        prev_element = element

    return {
        "full_sequence": full_sequence,
        "length": len(full_sequence),
        "annotations": annotations,
        "element_count": len(sorted_elements),
    }


def validate_construct(elements: list[ConstructElementSchema]) -> list[str]:
    """Validate construct element ordering and compatibility.

    Returns list of warning/error messages (empty if valid).
    """
    warnings = []
    sorted_elements = sorted(elements, key=lambda e: e.position)

    if not sorted_elements:
        warnings.append("Construct has no elements")
        return warnings

    # Check that CDS follows Kozak
    element_types = [e.element_type for e in sorted_elements]
    if "kozak" in element_types and "cds" in element_types:
        kozak_idx = element_types.index("kozak")
        cds_idx = element_types.index("cds")
        if cds_idx != kozak_idx + 1:
            warnings.append("CDS should immediately follow Kozak sequence")

    # Check that promoter comes first
    if element_types and element_types[0] != "promoter":
        warnings.append("Construct should begin with a promoter")

    # Check that construct ends with a terminator
    if element_types and element_types[-1] != "terminator":
        warnings.append("Construct should end with a terminator")

    return warnings
