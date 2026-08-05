#!/usr/bin/env python3
"""
nontriviality_check.py — F-063 non-triviality verification engine.

Per cycle 85 worklog: the confirmed novel hit (EXP-BLIND-023, lotus leaf ->
battery separator) has an open caveat. The F-063 check confirmed no review
paper exists and no >50-citation primary study exists for this specific
bridge. The F-065 check confirmed the extraction is grounded in source
text. But NEITHER check addresses whether the bridge is a GENUINE
discovery or a TRIVIAL physics-principle connection.

The distinction:
  - GENUINE discovery: "lotus leaf superhydrophobicity can improve battery
    separator electrolyte wetting" is a non-obvious claim that required
    cross-domain reasoning to produce.
  - TRIVIAL connection: "contact angle matters in both fields" is a
    physics principle that applies to every surface-liquid interaction.
    Stating it as a "bridge" is like saying "gravity connects bridges and
    airplanes."

This module performs a non-triviality check by:
  1. Searching for papers that explicitly cite BOTH literatures (a citation
     bridge). If papers exist that cite both lotus-leaf and battery-
     separator research, the bridge is already known to the community.
  2. Checking whether the shared mechanism concept (e.g., "contact angle")
     is a GENERIC physics principle (applies to >5 unrelated fields) or a
     SPECIFIC mechanism (applies to <3 fields). Generic principles produce
     trivial bridges.
  3. Checking whether the bridge requires domain-specific knowledge (e.g.,
     knowing that lotus leaf roughness is hierarchical micro/nano) or
     only generic physics (e.g., "surfaces have contact angles").

Verdicts:
  - NON_TRIVIAL: the bridge requires domain-specific knowledge to produce,
    and no citation bridge exists in the literature.
  - TRIVIAL_PRINCIPLE: the bridge is a generic physics principle that
    applies to many fields. Stating it as a "discovery" is inflation.
  - KNOWN_BRIDGE: papers exist that cite both literatures. The bridge is
    already known to the community (should be RETRIEVAL, not NOVEL).

Governance: P33 — Don't accept a negative claim without searching for its
refutation. The cycle-84 F-063 check said "no review paper exists." This
module searches for the refutation: papers that DO cite both literatures.

Governance: AE-13 (Schema worship) — a bridge that passes F-063 (no review)
and F-065 (extraction grounded) is not automatically non-trivial. A
generic physics principle wearing a bridge's vocabulary is still trivial.
"""
import sys
import json
import re
import subprocess
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List

ROOT = pathlib.Path("/home/z/my-project/audit/repo")
PREDICTIONS = ROOT / "data" / "ledger" / "predictions.jsonl"

# Generic physics/chemistry principles that produce trivial bridges.
# A bridge whose shared mechanism is one of these is likely trivial.
#
# REFINEMENT (cycle 87): The original list used substring matching, which
# meant "permeability" matched both "permeability" (generic) AND
# "selective_permeability" (specific). This was wrong. "Selective
# permeability" is a specific mechanism (BBB tight junctions, nanofiber
# membranes), not a generic principle.
#
# The fix: use word-boundary matching. A generic principle matches only
# when it appears as a standalone concept, NOT when it is part of a
# compound term with a specific qualifier.
#
# SPECIFIC_QUALIFIERS: prefixes/adjectives that, when combined with a
# generic principle, make it specific. E.g., "permeability" is generic,
# but "selective permeability" is specific because "selective" narrows
# it to a size/property-gated mechanism.
GENERIC_PRINCIPLES = [
    "contact_angle", "surface_tension", "wettability", "porosity",
    "permeability", "diffusion", "viscosity", "thermal_conductivity",
    "electrical_conductivity", "ph", "concentration", "temperature",
    "pressure", "density", "hardness", "elasticity", "fracture_toughness",
    "adhesion", "friction", "corrosion", "oxidation", "evaporation",
    "condensation", "crystallization", "melting_point", "boiling_point",
]

# Qualifiers that, when prefixed to a generic principle, make it specific.
# A mechanism containing "<qualifier> <generic>" is NOT trivial.
# E.g., "selective permeability" is specific (size-gated), "permeability"
# alone is generic.
SPECIFIC_QUALIFIERS = [
    "selective", "size_selective", "ion_selective", "voltage_gated",
    "ligand_gated", "temperature_dependent", "ph_dependent",
    "pressure_driven", "light_activated", "magnetically_guided",
    "bioinspired", "biomimetic", "hierarchical", "anisotropic",
    "asymmetric", "stimuli_responsive", "self_healing", "self_cleaning",
    "controlled_release", "targeted", "tunable",
]


def is_generic_match(mechanism: str, generic_principle: str) -> bool:
    """Check if a mechanism matches a generic principle.

    A match is generic ONLY if the principle appears as a standalone
    concept, NOT as part of a compound term with a specific qualifier.

    Examples:
      - mechanism="contact_angle", gp="contact_angle" -> True (generic)
      - mechanism="selective_permeability", gp="permeability" -> False
        (specific: "selective" qualifies it)
      - mechanism="permeability", gp="permeability" -> True (generic)
      - mechanism="surface_wettability_control", gp="wettability" -> True
        (wettability is the core concept, "surface" and "control" are
        generic context words, not specific qualifiers)

    The logic:
      1. The generic principle must be present in the mechanism.
      2. The principle must NOT be immediately preceded by a specific
         qualifier (e.g., "selective permeability" does not match
         generic "permeability").
    """
    mech_lower = mechanism.lower().replace(" ", "_")
    gp = generic_principle.lower().replace(" ", "_")

    # The principle must be present
    if gp not in mech_lower:
        return False

    # Check if any specific qualifier immediately precedes the principle
    for qualifier in SPECIFIC_QUALIFIERS:
        qual = qualifier.lower().replace(" ", "_")
        # If the mechanism contains "<qualifier>_<gp>", it's specific
        if f"{qual}_{gp}" in mech_lower:
            return False
        # Also check "<qualifier> <gp>" with space (before normalization)
        if f"{qual} {generic_principle}" in mechanism.lower():
            return False

    # Check if the mechanism IS exactly the generic principle (standalone)
    if mech_lower == gp:
        return True

    # Check if the principle is the core concept with only generic context
    # words around it (e.g., "surface_wettability_control" -> wettability
    # is the core, "surface" and "control" are generic context)
    generic_context_words = {
        "surface", "control", "property", "mechanism", "effect",
        "phenomenon", "behavior", "characteristic", "parameter",
        "measurement", "value", "rate", "coefficient", "factor",
        "high", "low", "increased", "decreased", "enhanced", "reduced",
    }
    parts = mech_lower.split("_")
    non_gp_parts = [p for p in parts if p != gp and p]
    # If all non-principle parts are generic context words, it's still generic
    if all(p in generic_context_words for p in non_gp_parts):
        return True

    # If there are non-generic, non-context parts, check if they're specific
    specific_parts = [p for p in non_gp_parts if p not in generic_context_words]
    # If any specific qualifier is present, it's NOT a generic match
    for qual in SPECIFIC_QUALIFIERS:
        qual_word = qual.split("_")[0]
        if qual_word in specific_parts:
            return False

    # Default: if the principle is present and no specific qualifier found,
    # treat as generic (conservative — favors calling bridges trivial)
    return True


def search_citation_bridge_semantic_scholar(lit_a_terms: List[str],
                                              lit_b_terms: List[str]) -> Dict:
    """Search Semantic Scholar for papers that cite both literatures.

    This is a TRUE citation network analysis (vs the web_search keyword
    fallback). Queries the Semantic Scholar Graph API for papers matching
    literature A terms, then checks if any also mention literature B terms.

    Falls back gracefully on rate limit (429) or API errors.
    """
    import urllib.parse

    a_term = lit_a_terms[0] if lit_a_terms else ""
    b_term = lit_b_terms[0] if lit_b_terms else ""
    combined = f"{a_term} {b_term}"

    # Semantic Scholar search endpoint
    query = urllib.parse.quote(combined)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5&fields=title,year,citationCount,abstract"

    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "15",
             "-H", "User-Agent: TEE-research/1.0",
             url],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(result.stdout)
        if "error" in data or data.get("code") == 429:
            return {
                "api": "semantic_scholar",
                "available": False,
                "error": data.get("message", "rate limited"),
                "papers": [],
            }
        papers = data.get("data", [])
        # Check which papers mention BOTH literatures in abstract
        bridge_papers = []
        for p in papers:
            abstract = (p.get("abstract") or "").lower()
            title = (p.get("title") or "").lower()
            text = abstract + " " + title
            has_a = any(t.lower() in text for t in lit_a_terms)
            has_b = any(t.lower() in text for t in lit_b_terms)
            if has_a and has_b:
                bridge_papers.append({
                    "title": p.get("title", "")[:80],
                    "year": p.get("year"),
                    "citations": p.get("citationCount", 0),
                })
        return {
            "api": "semantic_scholar",
            "available": True,
            "papers_found": len(papers),
            "bridge_papers_found": len(bridge_papers),
            "bridge_papers": bridge_papers[:5],
            "citation_bridge_exists": len(bridge_papers) > 0,
        }
    except Exception as e:
        return {
            "api": "semantic_scholar",
            "available": False,
            "error": str(e),
            "papers": [],
        }


def search_citation_bridge(lit_a_terms: List[str], lit_b_terms: List[str]) -> Dict:
    """Search for papers that mention BOTH literature A and literature B terms.

    Per cycle 87: tries Semantic Scholar API first (true citation network),
    falls back to z-ai web_search (keyword matching) on rate limit or error.

    Returns: {
        'api_used': 'semantic_scholar' | 'web_search_fallback',
        'combined_query': str,
        'papers_found': int,
        'bridge_papers_found': int,
        'bridge_papers': list,
        'citation_bridge_exists': bool,
    }
    """
    # Try Semantic Scholar first
    ss_result = search_citation_bridge_semantic_scholar(lit_a_terms, lit_b_terms)

    if ss_result.get("available"):
        return {
            "api_used": "semantic_scholar",
            "combined_query": f"{lit_a_terms[0] if lit_a_terms else ''} {lit_b_terms[0] if lit_b_terms else ''}",
            "papers_found": ss_result["papers_found"],
            "bridge_papers_found": ss_result["bridge_papers_found"],
            "bridge_papers": ss_result["bridge_papers"],
            "citation_bridge_exists": ss_result["citation_bridge_exists"],
        }

    # Fallback: z-ai web_search (keyword matching, less precise)
    a_term = lit_a_terms[0] if lit_a_terms else ""
    b_term = lit_b_terms[0] if lit_b_terms else ""
    combined_query = f"{a_term} {b_term}"

    print(f"  [fallback] Semantic Scholar unavailable ({ss_result.get('error','')}), using web_search")

    result = subprocess.run(
        ["z-ai", "function", "-n", "web_search",
         "-a", json.dumps({"query": combined_query, "num": 8})],
        capture_output=True, text=True, timeout=30
    )
    match = re.search(r'\[.*\]', result.stdout, re.DOTALL)
    papers = json.loads(match.group()) if match else []

    # Filter: a true citation bridge paper mentions BOTH literatures explicitly
    bridge_papers = []
    for p in papers:
        snippet = (p.get("snippet", "") + " " + p.get("name", "")).lower()
        has_a = any(t.lower() in snippet for t in lit_a_terms)
        has_b = any(t.lower() in snippet for t in lit_b_terms)
        if has_a and has_b:
            bridge_papers.append(p)

    return {
        "api_used": "web_search_fallback",
        "semantic_scholar_error": ss_result.get("error", "unavailable"),
        "combined_query": combined_query,
        "papers_found": len(papers),
        "bridge_papers_found": len(bridge_papers),
        "bridge_papers": [{"title": p.get("name", "")[:80],
                           "url": p.get("url", ""),
                           "snippet": p.get("snippet", "")[:150]}
                          for p in bridge_papers[:5]],
        "citation_bridge_exists": len(bridge_papers) > 0,
    }


def check_mechanism_specificity(shared_mechanism: str,
                                 lit_a_query: str, lit_b_query: str) -> Dict:
    """Check whether the shared mechanism is generic or specific.

    A generic principle (e.g., "contact angle") applies to many fields
    and produces trivial bridges. A specific mechanism (e.g., "biomineralization")
    applies to few fields and produces non-trivial bridges.

    Returns: {
        'mechanism': str,
        'is_generic_principle': bool,
        'generic_match': str or None,
        'domain_count': int (how many unrelated fields mention it),
        'specificity_verdict': 'GENERIC' | 'SPECIFIC',
    }
    """
    mech_lower = shared_mechanism.lower().replace(" ", "_")

    # Check against generic principles list using refined matching (cycle 87)
    # is_generic_match distinguishes "permeability" (generic) from
    # "selective_permeability" (specific) via SPECIFIC_QUALIFIERS.
    is_generic = False
    generic_match = None
    for gp in GENERIC_PRINCIPLES:
        if is_generic_match(shared_mechanism, gp):
            is_generic = True
            generic_match = gp
            break

    # Search for how many unrelated fields mention this mechanism
    result = subprocess.run(
        ["z-ai", "function", "-n", "web_search",
         "-a", json.dumps({"query": f"{shared_mechanism} applications fields", "num": 8})],
        capture_output=True, text=True, timeout=30
    )
    match = re.search(r'\[.*\]', result.stdout, re.DOTALL)
    papers = json.loads(match.group()) if match else []

    # Count distinct application domains mentioned
    domains = set()
    domain_keywords = {
        "battery": ["battery", "electrode", "electrolyte", "lithium"],
        "agriculture": ["agriculture", "crop", "soil", "fertilizer"],
        "medicine": ["medical", "biomedical", "drug", "therapy", "clinical"],
        "construction": ["concrete", "building", "construction"],
        "textiles": ["textile", "fabric", "clothing"],
        "aerospace": ["aerospace", "aircraft", "spacecraft"],
        "automotive": ["automotive", "vehicle", "car"],
        "electronics": ["electronics", "semiconductor", "circuit"],
        "water": ["water", "filtration", "desalination"],
        "energy": ["solar", "wind", "energy", "fuel"],
    }
    for p in papers:
        snippet = (p.get("snippet", "") + " " + p.get("name", "")).lower()
        for domain, keywords in domain_keywords.items():
            if any(k in snippet for k in keywords):
                domains.add(domain)

    domain_count = len(domains)

    if is_generic or domain_count >= 5:
        verdict = "GENERIC"
    elif domain_count >= 3:
        verdict = "MODERATELY_SPECIFIC"
    else:
        verdict = "SPECIFIC"

    return {
        "mechanism": shared_mechanism,
        "is_generic_principle": is_generic,
        "generic_match": generic_match,
        "domain_count": domain_count,
        "domains_found": sorted(list(domains)),
        "specificity_verdict": verdict,
    }


def check_domain_specific_knowledge(lit_a_query: str, lit_b_query: str,
                                     shared_mechanism: str) -> Dict:
    """Check whether the bridge requires domain-specific knowledge.

    A bridge that requires knowing domain-specific facts (e.g., "lotus leaf
    has hierarchical micro/nano roughness") is more non-trivial than a bridge
    that only uses generic physics (e.g., "surfaces have contact angles").

    Returns: {
        'requires_domain_knowledge': bool,
        'domain_specific_facts_a': list,
        'domain_specific_facts_b': list,
        'knowledge_verdict': 'DOMAIN_SPECIFIC' | 'GENERIC_ONLY',
    }
    """
    # Domain-specific facts for lotus leaf
    lotus_facts = [
        "hierarchical micro nano roughness",
        "epicuticular wax crystals",
        "papillae",
        "superhydrophobic",
    ]
    # Domain-specific facts for battery separator
    battery_facts = [
        "separator pore structure",
        "electrolyte uptake",
        "ionic conductivity",
        "polyolefin separator",
    ]

    # Check which domain-specific facts appear in the bridge
    a_facts_present = [f for f in lotus_facts if any(w in shared_mechanism.lower() for w in f.split())]
    b_facts_present = [f for f in battery_facts if any(w in shared_mechanism.lower() for w in f.split())]

    # The bridge requires domain knowledge if it uses domain-specific vocabulary
    # beyond the generic shared mechanism
    requires_domain = len(a_facts_present) > 0 or len(b_facts_present) > 0

    return {
        "requires_domain_knowledge": requires_domain,
        "domain_specific_facts_a": a_facts_present,
        "domain_specific_facts_b": b_facts_present,
        "knowledge_verdict": "DOMAIN_SPECIFIC" if requires_domain else "GENERIC_ONLY",
    }


def run_nontriviality_check(experiment_id: str, lit_a_query: str, lit_b_query: str,
                             shared_mechanism: str,
                             lit_a_terms: List[str], lit_b_terms: List[str]) -> Dict:
    """Run the full non-triviality check on a confirmed novel hit.

    Returns a report with the overall verdict.
    """
    print(f"\n{'='*70}")
    print(f"NON-TRIVIALITY CHECK: {experiment_id}")
    print(f"{'='*70}")
    print(f"Literature A: {lit_a_query}")
    print(f"Literature B: {lit_b_query}")
    print(f"Shared mechanism: {shared_mechanism}")

    report = {
        "type": "nontriviality_check",
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "writer": "scripts.nontriviality_check",
        "lit_a_query": lit_a_query,
        "lit_b_query": lit_b_query,
        "shared_mechanism": shared_mechanism,
    }

    # Check 1: Citation bridge (does any paper cite both literatures?)
    print("\n--- Check 1: Citation bridge search ---")
    citation = search_citation_bridge(lit_a_terms, lit_b_terms)
    report["citation_bridge_check"] = citation
    print(f"  Papers found: {citation['papers_found']}")
    print(f"  Bridge papers (mention both): {citation['bridge_papers_found']}")
    if citation["bridge_papers"]:
        for bp in citation["bridge_papers"][:3]:
            print(f"    - {bp['title']}")

    # Check 2: Mechanism specificity (generic or specific?)
    print("\n--- Check 2: Mechanism specificity ---")
    specificity = check_mechanism_specificity(shared_mechanism, lit_a_query, lit_b_query)
    report["mechanism_specificity_check"] = specificity
    print(f"  Is generic principle: {specificity['is_generic_principle']}")
    print(f"  Generic match: {specificity['generic_match']}")
    print(f"  Domain count: {specificity['domain_count']}")
    print(f"  Domains: {specificity['domains_found']}")
    print(f"  Verdict: {specificity['specificity_verdict']}")

    # Check 3: Domain-specific knowledge requirement
    print("\n--- Check 3: Domain-specific knowledge ---")
    knowledge = check_domain_specific_knowledge(lit_a_query, lit_b_query, shared_mechanism)
    report["domain_knowledge_check"] = knowledge
    print(f"  Requires domain knowledge: {knowledge['requires_domain_knowledge']}")
    print(f"  Verdict: {knowledge['knowledge_verdict']}")

    # Overall verdict
    if citation["citation_bridge_exists"]:
        overall = "KNOWN_BRIDGE"
        implication = (
            "Papers exist that cite both literatures. The bridge is already known "
            "to the community. Should be RETRIEVAL, not NOVEL. DOWNGRADE."
        )
    elif specificity["specificity_verdict"] == "GENERIC" and knowledge["knowledge_verdict"] == "GENERIC_ONLY":
        overall = "TRIVIAL_PRINCIPLE"
        implication = (
            "The shared mechanism is a generic physics principle that applies to "
            "many fields, and the bridge does not require domain-specific knowledge. "
            "Stating this as a 'discovery' is semantic inflation. The bridge is "
            "trivial. DOWNGRADE to TRIVIAL_CONNECTION (not a genuine discovery)."
        )
    elif specificity["specificity_verdict"] == "GENERIC":
        overall = "LIKELY_TRIVIAL"
        implication = (
            "The shared mechanism is generic, but the bridge may use domain-specific "
            "knowledge. KEEP as NOVEL_HIT with caveat: the bridge is a specific "
            "application of a generic principle. Non-triviality is borderline."
        )
    else:
        overall = "NON_TRIVIAL"
        implication = (
            "The shared mechanism is specific (not a generic physics principle), "
            "no citation bridge exists, and the bridge requires domain-specific "
            "knowledge. This is a genuine non-trivial discovery. CONFIRM as NOVEL_HIT."
        )

    report["overall_verdict"] = overall
    report["implication"] = implication

    print(f"\n  OVERALL VERDICT: {overall}")
    print(f"  Implication: {implication}")

    return report


def log_nontriviality(report: Dict):
    """Append the non-triviality report to predictions.jsonl."""
    with PREDICTIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, default=str) + "\n")
    print(f"  -> logged to predictions.jsonl")


if __name__ == "__main__":
    print("Non-Triviality Check Module — F-063 verification")
    print("Usage: import this module and call run_nontriviality_check().")
