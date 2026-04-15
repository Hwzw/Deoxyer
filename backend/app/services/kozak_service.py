"""Kozak sequence generation for different organisms.

Loads organism-specific Kozak consensus sequences from CSV data file.
"""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Load Kozak data from CSV at import time
_KOZAK_DATA: list[dict] = []


def _load_kozak_data() -> list[dict]:
    global _KOZAK_DATA
    if _KOZAK_DATA:
        return _KOZAK_DATA

    csv_path = DATA_DIR / "kozak_sequences.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Collect non-empty combinations
            combinations = []
            for i in range(1, 9):
                val = row.get(f"Combination {i}", "").strip()
                if val and not val.startswith("Lots of"):
                    combinations.append(val.upper())

            _KOZAK_DATA.append({
                "organism": row["Organism"].strip(),
                "clade": row.get("Clade/Group", "").strip(),
                "organism_type": row.get("Organism Type", "").strip(),
                "consensus": row.get("Kozak Consensus", "").strip(),
                "combinations": combinations,
            })

    return _KOZAK_DATA


# Map common tax IDs to CSV organism names for lookup
_TAX_ID_MAP = {
    # Vertebrates
    9606: "Vertebrate",
    10090: "Vertebrate",
    10116: "Vertebrate",
    9913: "Vertebrate",
    9031: "Vertebrate",
    7955: "Vertebrate",
    # Drosophila
    7227: "Fruit fly",
    # Yeast
    4932: "Budding yeast",
    28985: "Budding yeast",  # K. lactis — similar Kozak to S. cerevisiae
    # Plants
    3702: "Terrestrial plants",
    4577: "Terrestrial plants",  # Zea mays
    4530: "Terrestrial plants",  # Oryza sativa
    # Green algae
    3055: "Microalga",  # Chlamydomonas
    # Slime mold
    44689: "Slime mold",
    # Plasmodium
    5833: "Malarial",
    36329: "Malarial",
    # Toxoplasma
    5811: "Toxoplasma",
    # Ciliates
    5888: "Ciliate",  # Paramecium
    5911: "Ciliate",  # Tetrahymena
    # Trypanosomatidae
    5691: "Trypanosomatidae",  # Trypanosoma
    5660: "Trypanosomatidae",  # Leishmania
    # E. coli — uses Shine-Dalgarno, not Kozak
    562: None,
}


def _find_kozak_entry(organism_tax_id: int) -> dict | None:
    """Find the best matching Kozak entry for a given tax ID."""
    data = _load_kozak_data()

    # Check tax ID map first
    search_term = _TAX_ID_MAP.get(organism_tax_id)
    if search_term is None and organism_tax_id in _TAX_ID_MAP:
        # Explicitly mapped to None (e.g., E. coli)
        return None

    if search_term:
        for entry in data:
            if search_term.lower() in entry["organism"].lower():
                return entry

    # No match found — return None so caller can warn about defaulting
    return None


# Shine-Dalgarno for prokaryotes
_SHINE_DALGARNO = {
    "consensus": "AGGAGGATGG",
    "notes": "E. coli Shine-Dalgarno + start codon",
    "organism": "E. coli",
}


def generate_kozak(organism_tax_id: int, start_codon: str = "ATG") -> dict:
    """Generate appropriate Kozak/initiation sequence for target organism.

    Returns dict with consensus, sequence, organism info, and notes.
    """
    # E. coli and other prokaryotes use Shine-Dalgarno
    if organism_tax_id == 562:
        sequence = _SHINE_DALGARNO["consensus"]
        if start_codon != "ATG":
            idx = sequence.rfind("ATG")
            if idx >= 0:
                sequence = sequence[:idx] + start_codon + sequence[idx + 3:]
        return {
            "organism_tax_id": organism_tax_id,
            "organism": _SHINE_DALGARNO["organism"],
            "consensus": _SHINE_DALGARNO["consensus"],
            "sequence": sequence,
            "notes": _SHINE_DALGARNO["notes"],
        }

    entry = _find_kozak_entry(organism_tax_id)
    if not entry:
        # Fallback to vertebrate consensus
        return {
            "organism_tax_id": organism_tax_id,
            "organism": "Unknown (defaulting to vertebrate)",
            "consensus": "GCCACCATGG",
            "sequence": "GCCACCATGG" if start_codon == "ATG" else "GCCACC" + start_codon + "G",
            "notes": "Default vertebrate Kozak (organism not in database)",
        }

    consensus = entry["consensus"]
    # Use the first concrete combination as the sequence
    if entry["combinations"]:
        sequence = entry["combinations"][0]
    else:
        sequence = consensus.upper()

    # Replace only the start codon (last ATG in Kozak context)
    if start_codon != "ATG":
        idx = sequence.upper().rfind("ATG")
        if idx >= 0:
            sequence = sequence[:idx] + start_codon + sequence[idx + 3:]

    organism_name = entry["organism"]
    return {
        "organism_tax_id": organism_tax_id,
        "organism": organism_name,
        "consensus": consensus,
        "sequence": sequence,
        "notes": f"{organism_name} Kozak consensus from {entry['clade']}",
        "combinations": entry["combinations"],
    }
