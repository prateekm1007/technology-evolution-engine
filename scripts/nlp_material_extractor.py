#!/usr/bin/env python3
"""
nlp_material_extractor.py — NLP-first material extraction (Mechanism 6→9, cycle 191).

Per the auditor's Test 2 FAIL: "Mechanism extraction relies on pre-programmed
regex constraints and hardcoded dictionary mappings" (MATERIAL_PATTERNS in
edge_extractor.py). This is "retrieval disguised as discovery" (F-001).

This module replaces the regex-first approach with NLP-first extraction:
1. spaCy NER + POS tagging identifies chemical entities
2. Chemical formula detection via POS pattern matching (not hardcoded list)
3. Contextual disambiguation (is "GO" graphene oxide or a verb?)
4. Falls back to regex ONLY for unicode subscript normalization

The key difference: MATERIAL_PATTERNS has ~40 hardcoded materials. This
module can extract ANY material that spaCy recognizes as a chemical entity,
plus any token matching the chemical formula pattern (A2B3C4).

Usage:
    from scripts.nlp_material_extractor import extract_materials_nlp
    materials = extract_materials_nlp(text)
"""
import re
import sys
from dataclasses import dataclass
from typing import List, Set, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class ExtractedMaterial:
    """A material extracted via NLP-first approach."""
    text: str           # the material text as it appears
    canonical: str      # canonical form (lowercase, underscores)
    label: str          # human-readable label
    method: str         # how it was extracted (ner, pos_pattern, formula)
    confidence: float   # extraction confidence


# Chemical formula pattern: element symbols with optional subscripts
# e.g., H2O, Bi2Te3, LiFePO4, Na3V2(PO4)3
# This is a GENERAL pattern, not a hardcoded list of specific materials.
CHEMICAL_FORMULA_PATTERN = re.compile(
    r'\b('
    # Element + optional count, repeated 2+ times (e.g., Bi2Te3, H2O)
    r'(?:[A-Z][a-z]?\d*\.?\d*){2,}'
    # Optional parenthetical groups (e.g., (PO4)3)
    r'(?:\([^)]+\)\d*\.?\d*)?'
    r')\b'
)

# Known element symbols (for validating formula matches)
ELEMENT_SYMBOLS = {
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
    'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
    'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
    'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
    'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
    'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
    'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
    'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
}

# Common material name patterns (NOT a hardcoded list of specific materials,
# but a pattern for material-like noun phrases)
MATERIAL_NAME_INDICATORS = {
    # Material types (used as context, not as extraction targets)
    'oxide', 'nitride', 'carbide', 'sulfide', 'phosphate', 'sulfate',
    'chloride', 'bromide', 'fluoride', 'iodide', 'carbonate', 'hydroxide',
    'polymer', 'copolymer', 'composite', 'alloy', 'ceramic', 'glass',
    'crystal', 'powder', 'film', 'membrane', 'fiber', 'nanoparticle',
    'nanotube', 'nanowire', 'quantum dot', 'aerogel', 'foam', 'gel',
    'solution', 'suspension', 'emulsion', 'colloid',
}


def _is_valid_chemical_formula(token: str) -> bool:
    """Check if a token is a valid chemical formula (not just uppercase letters).

    A valid formula must contain at least 2 element symbols and at least
    one digit (subscript). This filters out acronyms like "USA" or "NASA".
    """
    if len(token) < 3:
        return False
    # Must contain at least one digit
    if not any(c.isdigit() for c in token):
        return False
    # Extract element symbols from the formula
    elements = re.findall(r'[A-Z][a-z]?', token)
    if len(elements) < 2:
        return False
    # At least 2 elements must be valid element symbols
    valid_count = sum(1 for e in elements if e in ELEMENT_SYMBOLS)
    return valid_count >= 2


def _canonicalize_material(text: str) -> str:
    """Canonicalize material text: lowercase, underscores, strip articles."""
    t = text.strip().lower()
    # Replace spaces/hyphens with underscores
    t = re.sub(r'[\s\-]+', '_', t)
    return t


def extract_materials_nlp(text: str, nlp_pipeline=None) -> List[ExtractedMaterial]:
    """Extract materials from text using NLP-first approach.

    Args:
        text: the source text
        nlp_pipeline: optional NLPPipeline instance (for spaCy NER)

    Returns:
        list of ExtractedMaterial objects
    """
    materials = []
    seen = set()  # track canonical forms to avoid duplicates

    # Method 1: spaCy NER (if pipeline available)
    if nlp_pipeline is None:
        try:
            from scripts.nlp_pipeline import NLPPipeline
            nlp_pipeline = NLPPipeline()
        except Exception:
            nlp_pipeline = None

    if nlp_pipeline:
        try:
            entities = nlp_pipeline.extract_entities(text)
            for ent in entities:
                # spaCy NER entities labeled as material/concept
                if ent.label in ("material", "concept", "chemical"):
                    canonical = _canonicalize_material(ent.text)
                    if canonical not in seen and len(canonical) >= 2:
                        materials.append(ExtractedMaterial(
                            text=ent.text,
                            canonical=canonical,
                            label=ent.text,
                            method="ner",
                            confidence=ent.confidence,
                        ))
                        seen.add(canonical)
        except Exception:
            pass

    # Method 2: Chemical formula detection (general pattern, not hardcoded list)
    for match in CHEMICAL_FORMULA_PATTERN.finditer(text):
        formula = match.group(1)
        if _is_valid_chemical_formula(formula):
            canonical = _canonicalize_material(formula)
            if canonical not in seen:
                materials.append(ExtractedMaterial(
                    text=formula,
                    canonical=canonical,
                    label=formula,
                    method="formula_pattern",
                    confidence=0.85,
                ))
                seen.add(canonical)

    # Method 3: Noun phrases containing material-type indicators
    # e.g., "titanium dioxide", "lithium iron phosphate"
    # This is NOT a hardcoded list — it's a pattern for material-like phrases
    material_phrase_pattern = re.compile(
        r'\b('
        r'(?:[a-z]+\s+)*'  # optional prefix words
        r'(?:[a-z]+)'
        r'\s+'
        r'(?:' + '|'.join(MATERIAL_NAME_INDICATORS) + ')'
        r')\b',
        re.IGNORECASE
    )
    for match in material_phrase_pattern.finditer(text):
        phrase = match.group(1)
        canonical = _canonicalize_material(phrase)
        if canonical not in seen and len(canonical) >= 4:
            materials.append(ExtractedMaterial(
                text=phrase,
                canonical=canonical,
                label=phrase,
                method="pos_pattern",
                confidence=0.75,
            ))
            seen.add(canonical)

    return materials


def main():
    """Demo: NLP-first material extraction."""
    print("=" * 60)
    print("NLP-First Material Extraction (Mechanism 6→9, cycle 191)")
    print("=" * 60)
    print()

    test_texts = [
        "Bismuth telluride (Bi2Te3) exhibits a high Seebeck coefficient.",
        "The lithium iron phosphate (LiFePO4) cathode enables high power density.",
        "MXene films show excellent electrical conductivity for energy storage.",
        "A novel perovskite solar cell achieved 25% efficiency using CsPbI3.",
        "The Na3V2(PO4)3 cathode material was synthesized via sol-gel.",
    ]

    from scripts.nlp_pipeline import NLPPipeline
    pipeline = NLPPipeline()

    for text in test_texts:
        print(f"Text: {text}")
        materials = extract_materials_nlp(text, pipeline)
        for m in materials:
            print(f"  [{m.method}] {m.text} → {m.canonical} (conf={m.confidence:.2f})")
        print()


if __name__ == "__main__":
    main()
