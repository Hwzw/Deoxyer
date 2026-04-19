"""DNA and protein sequence utilities using Biopython."""

from Bio.Seq import Seq

VALID_DNA = set("ATCGatcg")
# 20 standard + stop + IUPAC ambiguity codes (B=Asx, X=any, Z=Glx, U=Sec, O=Pyl).
VALID_PROTEIN = set("ACDEFGHIKLMNPQRSTVWYBXZUOacdefghiklmnpqrstvwybxzuo*")

COMPLEMENT = str.maketrans("ATCGatcg", "TAGCtagc")


def validate_dna(sequence: str) -> bool:
    return all(c in VALID_DNA for c in sequence)


def validate_protein(sequence: str) -> bool:
    return all(c in VALID_PROTEIN for c in sequence)


def reverse_complement(sequence: str) -> str:
    return sequence.translate(COMPLEMENT)[::-1]


def gc_content(sequence: str) -> float:
    if not sequence:
        return 0.0
    seq_upper = sequence.upper()
    gc_count = seq_upper.count("G") + seq_upper.count("C")
    return gc_count / len(seq_upper)


def translate(dna_sequence: str) -> str:
    seq = Seq(dna_sequence)
    return str(seq.translate())


def reverse_translate(protein_sequence: str, codon_table: dict) -> str:
    """Reverse translate protein to DNA using most frequent codons from a usage table."""
    dna = []
    for aa in protein_sequence.upper():
        if aa == "*":
            break
        # Find the most frequent codon for this amino acid
        best_codon = None
        best_freq = -1.0
        for amino_acid, codons in codon_table.items():
            if amino_acid == aa:
                for codon, freq in codons.items():
                    if freq > best_freq:
                        best_freq = freq
                        best_codon = codon
        if best_codon:
            dna.append(best_codon)
        else:
            dna.append("NNN")  # unknown amino acid
    return "".join(dna)


def detect_sequence_type(sequence: str) -> str:
    """Detect if a sequence is DNA or protein."""
    clean = sequence.upper().replace(" ", "").replace("\n", "")
    if not clean:
        return "unknown"
    dna_chars = set("ATCGN")
    if all(c in dna_chars for c in clean):
        return "dna"
    return "protein"
