#!/usr/bin/env python3
"""
alias_resolver.py — Abbreviation-based alias resolution for Gen 2.

Per cycle 159: the scoring says "No alias resolution beyond prefix/suffix
stripping (0)". The coreference resolver handles substring matching but
not ABBREVIATION resolution — e.g., "vertical graphene nanosheets (VGN)"
should create an alias between "vertical graphene nanosheets" and "VGN".

This module provides abbreviation-based alias resolution:
1. Finds patterns like "Full Name (ABBR)" or "ABBR (Full Name)"
2. Creates aliases between the abbreviation and the full name
3. Merges entities that are aliases of each other

Usage:
    from scripts.alias_resolver import resolve_abbreviations
    entities = resolve_abbreviations(entities, text)
"""
import re
from typing import List, Tuple, Dict
from dataclasses import dataclass


def find_abbreviations(text: str) -> List[Tuple[str, str]]:
    """Find abbreviation-definition pairs in text.

    Patterns:
    - "Full Name (FN)" → alias("Full Name", "FN")
    - "FN (Full Name)" → alias("FN", "Full Name")

    Returns list of (full_name, abbreviation) tuples.
    """
    abbreviations = []

    # Pattern 1: "Full Name (ABBR)" — ABBR is 2-6 uppercase letters
    # e.g., "vertical graphene nanosheets (VGN)"
    pattern1 = re.compile(
        r'([A-Z][\w\s\-]{3,40}?)\s*\(([A-Z]{2,6})\)'
    )
    for match in pattern1.finditer(text):
        full_name = match.group(1).strip()
        abbr = match.group(2).strip()
        # Verify: the abbreviation should match the first letters of the words
        words = full_name.split()
        if len(words) >= 2:
            expected_abbr = ''.join(w[0].upper() for w in words if w[0].isalpha())
            if abbr in expected_abbr or expected_abbr.startswith(abbr):
                abbreviations.append((full_name, abbr))

    # Pattern 2: "ABBR (Full Name)" — ABBR is 2-6 uppercase letters
    pattern2 = re.compile(
        r'\b([A-Z]{2,6})\s*\(([A-Z][\w\s\-]{3,40}?)\)'
    )
    for match in pattern2.finditer(text):
        abbr = match.group(1).strip()
        full_name = match.group(2).strip()
        words = full_name.split()
        if len(words) >= 2:
            expected_abbr = ''.join(w[0].upper() for w in words if w[0].isalpha())
            if abbr in expected_abbr or expected_abbr.startswith(abbr):
                abbreviations.append((full_name, abbr))

    return abbreviations


def resolve_abbreviations(entities: List, text: str) -> List:
    """Resolve abbreviation aliases in the entity list.

    For each abbreviation pair found in the text, merge entities that
    match either the full name or the abbreviation. The merged entity
    gets both names as aliases.
    """
    from scripts.nlp_pipeline import ExtractedEntity

    abbreviations = find_abbreviations(text)
    if not abbreviations:
        return entities

    # Build a mapping: alias_text → canonical_entity
    alias_map: Dict[str, any] = {}
    for full_name, abbr in abbreviations:
        full_lower = full_name.lower().strip()
        abbr_lower = abbr.lower().strip()
        alias_map[full_lower] = None  # placeholder
        alias_map[abbr_lower] = None

    # Find entities that match full names or abbreviations
    for ent in entities:
        ent_lower = ent.text.lower().strip()
        if ent_lower in alias_map:
            alias_map[ent_lower] = ent
        # Also check if entity text contains the full name or abbr
        for full_name, abbr in abbreviations:
            full_lower = full_name.lower().strip()
            abbr_lower = abbr.lower().strip()
            if ent_lower == full_lower or ent_lower == abbr_lower:
                alias_map[ent_lower] = ent

    # Merge: for each abbreviation pair, if both full name and abbr have entities,
    # merge them (keep the longer one, add the shorter as alias)
    merged_entities = list(entities)
    for full_name, abbr in abbreviations:
        full_lower = full_name.lower().strip()
        abbr_lower = abbr.lower().strip()
        full_ent = alias_map.get(full_lower)
        abbr_ent = alias_map.get(abbr_lower)

        if full_ent and abbr_ent and full_ent is not abbr_ent:
            # Merge: keep the full name (more descriptive), add abbreviation as alias
            if abbr not in full_ent.aliases:
                full_ent.aliases.append(abbr)
            # Remove the abbreviation entity from the list (it's now an alias)
            if abbr_ent in merged_entities:
                merged_entities.remove(abbr_ent)

    return merged_entities


def main():
    """Demo: abbreviation resolution."""
    text = """
    Vertical graphene nanosheets (VGN) were synthesized by microwave plasma
    enhanced chemical vapor deposition. The VGN showed excellent
    electrochemical performance. Among electrolytes, H2SO4 exhibited
    the best capacitance.
    """

    print("Text:")
    print(text)
    print()

    abbreviations = find_abbreviations(text)
    print(f"Abbreviations found: {len(abbreviations)}")
    for full, abbr in abbreviations:
        print(f"  {full!r} ↔ {abbr!r}")


if __name__ == "__main__":
    main()
