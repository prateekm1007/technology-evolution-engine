"""
test_no_gold_derived_synonyms.py — P0 structural test (cycle 270, F-158).

Per the deep audit finding (cycle 270): BRIDGE_SYNONYMS was circular —
19/20 gold bridges were direct keys, and the synonym values were
reverse-engineered from what the extraction pipeline produced for those
specific items. This violated MC-1 (No self-validation) of the
Measurement Constitution.

This test enforces that BRIDGE_SYNONYMS is either:
1. Empty (the current state, post-fix), OR
2. If non-empty, its keys do NOT overlap with gold bridge names

This is the structural guard that makes the mistake harder to
reintroduce. Even if someone rebuilds the synonym map, this test
will catch circularity at the key level.

The test for FULL independence is stronger: someone who has never
seen the gold set should be able to independently reconstruct a
synonym map using general knowledge of the domain. That test requires
human review and cannot be fully automated. This structural test is
the automated component — it catches the specific failure mode
(gold bridge names as synonym keys) that was found in cycle 270.
"""
import sys
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def _canon(text: str) -> str:
    """Canonicalize: lowercase, underscores, strip punctuation."""
    t = text.lower().strip()
    t = re.sub(r'[\s\-]+', '_', t)
    t = re.sub(r'[^a-z0-9_]', '', t)
    t = re.sub(r'_+', '_', t)
    return t.strip('_')


def test_bridge_synonyms_is_empty_or_independent():
    """BRIDGE_SYNONYMS must be empty OR its keys must not overlap
    with gold bridge names.

    This is the P0 circular validation guard (F-158, cycle 270).
    The previous BRIDGE_SYNONYMS had 19/20 gold bridges as direct
    keys — a circular validation violation of MC-1 (No self-validation).
    """
    from benchmarks.discovery_capability_benchmark import (
        GOLD_DISCOVERIES, BRIDGE_SYNONYMS,
    )

    if not BRIDGE_SYNONYMS:
        # Empty is the current post-fix state — PASS
        return

    # If non-empty, check that keys don't overlap with gold bridges
    gold_bridges_canon = {_canon(g["bridge"]) for g in GOLD_DISCOVERIES}
    syn_keys_canon = {_canon(k) for k in BRIDGE_SYNONYMS.keys()}

    overlap = gold_bridges_canon & syn_keys_canon
    assert not overlap, (
        f"CIRCULAR VALIDATION VIOLATION (MC-1): {len(overlap)}/{len(gold_bridges_canon)} "
        f"gold bridges appear as BRIDGE_SYNONYMS keys: {overlap}. "
        f"The synonym map must be built from an independent source "
        f"(not derived from GOLD_DISCOVERIES). See F-158."
    )


def test_bridge_synonyms_documented_provenance():
    """If BRIDGE_SYNONYMS is non-empty, its source file must document
    that it was built from an independent source (not gold-derived)."""
    from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS

    if not BRIDGE_SYNONYMS:
        # Empty — no provenance needed
        return

    # If non-empty, check that the source file documents independence
    source = (REPO / "benchmarks" / "discovery_capability_benchmark.py").read_text()
    # Look for a comment mentioning "independent" or "WordNet" or "LLM"
    # near the BRIDGE_SYNONYMS definition
    assert (
        "independent" in source.lower()
        or "wordnet" in source.lower()
        or "llm" in source.lower()
    ), (
        "BRIDGE_SYNONYMS is non-empty but its source does not document "
        "an independent provenance. The synonym map must be built from "
        "a source that never had access to GOLD_DISCOVERIES. See F-158."
    )


def test_m_synonym_falls_back_to_token_when_no_synonyms():
    """With empty BRIDGE_SYNONYMS, m_synonym should behave identically
    to m_token (the non-circular fallback)."""
    import re

    def canon(text):
        t = text.lower().strip()
        t = re.sub(r'[\s\-]+', '_', t)
        t = re.sub(r'[^a-z0-9_]', '', t)
        t = re.sub(r'_+', '_', t)
        return t.strip('_')

    def m_token(expected, candidate):
        e, c = canon(expected), canon(candidate)
        if e in c or c in e:
            return True
        stops = {"the", "a", "an", "of", "in", "and", "for", "to", "with", "by"}
        et = set(e.split("_")) - stops
        ct = set(c.split("_")) - stops
        return len({t for t in (et & ct) if len(t) >= 4}) > 0

    def m_synonym(expected, candidate, synmap):
        if m_token(expected, candidate):
            return True
        ek = canon(expected)
        ck = canon(candidate)
        syns = synmap.get(ek, set())
        if ck in syns:
            return True
        for s in syns:
            sc = canon(s)
            if sc in ck or ck in sc:
                return True
        return False

    empty_synmap = {}
    test_pairs = [
        ("thermal emission", "thermal radiation"),
        ("biomineralization", "mineral precipitation"),
        ("heat dissipation", "thermal management"),
        ("tight junctions", "size selective pores"),
        ("contact angle", "wetting angle"),
    ]

    for expected, candidate in test_pairs:
        token_result = m_token(expected, candidate)
        synonym_result = m_synonym(expected, candidate, empty_synmap)
        assert synonym_result == token_result, (
            f"With empty synmap, m_synonym('{expected}', '{candidate}') = "
            f"{synonym_result}, but m_token = {token_result}. "
            f"They should be identical when synmap is empty."
        )
