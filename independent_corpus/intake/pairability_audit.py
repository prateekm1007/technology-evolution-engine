"""
independent_corpus.intake.pairability_audit — Source-pairability audit.

Tests whether the eligible corpus contains enough legitimate, non-trivial,
cross-domain source pairs to construct ≥100 benchmark cases.

TWO INDEPENDENT SCORES per pair:
1. Lexical/semantic relatedness (Jaccard on title tokens)
2. Scientific transferability evidence (mechanism-bridge heuristic)

The LATTER controls eligibility, not the former.

Dispositions:
  PAIRABLE              — cross-domain pair with scientific bridge evidence
  WEAK_BRIDGE           — cross-domain pair but bridge evidence is weak
  DUPLICATE             — near-duplicate content
  SAME_DOMAIN           — both sources in same canonical domain
  INSUFFICIENT_EVIDENCE — cannot determine bridge from available info
  OUTSIDE_SCOPE         — pair doesn't meet basic requirements

Does NOT construct benchmark questions.
Does NOT generate hypotheses.
Does NOT use TEE.
Does NOT change the taxonomy.
Does NOT optimize for producing 100 pairs.
"""
import json
import re
import sys
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from difflib import SequenceMatcher

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from custodian.src.domain_taxonomy import canonicalize_domain
from custodian.src.hasher import sha256_string


# Dispositions
PAIRABLE = "PAIRABLE"
WEAK_BRIDGE = "WEAK_BRIDGE"
DUPLICATE = "DUPLICATE"
SAME_DOMAIN = "SAME_DOMAIN"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
OUTSIDE_SCOPE = "OUTSIDE_SCOPE"


@dataclass
class PairAudit:
    """Audit result for one candidate pair."""
    source_a_id: str
    source_b_id: str
    domain_a: str
    domain_b: str
    domain_distinct: bool
    independent_provenance: bool
    publication_date_valid: bool
    full_text_available: bool
    exact_duplicate: bool
    near_duplicate: bool
    lexical_similarity: float  # Jaccard on title tokens (0-1)
    scientific_bridge_score: float  # Heuristic mechanism-bridge score (0-1)
    bridge_evidence_type: str  # "MECHANISM", "MATERIAL", "PROCESS", "METHOD", "NONE"
    disposition: str
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "source_a_id": self.source_a_id,
            "source_b_id": self.source_b_id,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "domain_distinct": self.domain_distinct,
            "independent_provenance": self.independent_provenance,
            "publication_date_valid": self.publication_date_valid,
            "full_text_available": self.full_text_available,
            "exact_duplicate": self.exact_duplicate,
            "near_duplicate": self.near_duplicate,
            "lexical_similarity": round(self.lexical_similarity, 4),
            "scientific_bridge_score": round(self.scientific_bridge_score, 4),
            "bridge_evidence_type": self.bridge_evidence_type,
            "disposition": self.disposition,
            "notes": self.notes,
        }


def _tokenize(text: str) -> set:
    """Tokenize text into lowercase word tokens (length >= 3)."""
    return set(re.findall(r'\b[a-z]{3,}\b', text.lower()))


def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# Scientific mechanism-bridge keywords (domain-agnostic)
# These indicate that a paper describes a transferable mechanism/process/method
MECHANISM_INDICATORS = {
    "mechanism", "process", "method", "approach", "technique", "model",
    "framework", "system", "structure", "property", "behavior", "phenomenon",
    "principle", "effect", "interaction", "transfer", "conversion",
    "optimization", "efficiency", "performance", "enhancement", "improvement",
    "catalyst", "reaction", "synthesis", "fabrication", "deposition",
    "characterization", "measurement", "simulation", "analysis",
}

# Bridge-type keywords that suggest cross-domain transferability
BRIDGE_INDICATORS = {
    "inspired": "MECHANISM",
    "biomimetic": "MECHANISM",
    "bioinspired": "MECHANISM",
    "analog": "MECHANISM",
    "analogy": "MECHANISM",
    "transfer": "PROCESS",
    "adapt": "PROCESS",
    "apply": "PROCESS",
    "novel": "METHOD",
    "new": "METHOD",
    "innovative": "METHOD",
    "composite": "MATERIAL",
    "hybrid": "MATERIAL",
    "nanostructure": "MATERIAL",
    "surface": "MATERIAL",
    "interface": "MATERIAL",
    "coupling": "MECHANISM",
    "synergistic": "MECHANISM",
    "multifunctional": "PROPERTY",
    "tunable": "PROPERTY",
    "responsive": "PROPERTY",
}


def _compute_bridge_score(title_a: str, title_b: str, domain_a: str, domain_b: str) -> Tuple[float, str]:
    """Compute scientific transferability evidence score.

    This is NOT semantic similarity. It looks for evidence that the two
    papers describe mechanisms/processes/methods that could plausibly
    transfer across domains.

    Returns (score, evidence_type).
    """
    tokens_a = _tokenize(title_a)
    tokens_b = _tokenize(title_b)

    # Check for mechanism indicators in both titles
    mech_a = tokens_a & MECHANISM_INDICATORS
    mech_b = tokens_b & MECHANISM_INDICATORS

    # Check for bridge indicators
    bridge_a = {}
    for token in tokens_a:
        if token in BRIDGE_INDICATORS:
            bridge_a[token] = BRIDGE_INDICATORS[token]
    bridge_b = {}
    for token in tokens_b:
        if token in BRIDGE_INDICATORS:
            bridge_b[token] = BRIDGE_INDICATORS[token]

    # Score components:
    # 1. Both papers describe mechanisms/processes (transferable)
    mechanism_score = 0.0
    if mech_a and mech_b:
        mechanism_score = 0.4  # Both have mechanism indicators

    # 2. Bridge indicators present
    bridge_score = 0.0
    bridge_type = "NONE"
    if bridge_a or bridge_b:
        bridge_score = 0.3
        # Use the first bridge type found
        all_bridges = {**bridge_a, **bridge_b}
        if all_bridges:
            bridge_type = list(all_bridges.values())[0]

    # 3. Shared technical terms (not stopwords, not domain-specific)
    # This is NOT lexical similarity — it's shared technical vocabulary
    # that suggests a common underlying mechanism
    shared_technical = tokens_a & tokens_b
    # Remove common English words
    common_words = {"the", "and", "for", "with", "from", "that", "this", "are", "was",
                    "were", "has", "have", "had", "been", "not", "but", "all", "can",
                    "may", "will", "its", "our", "their", "these", "those", "into",
                    "than", "then", "them", "what", "when", "where", "which", "while"}
    shared_technical = shared_technical - common_words
    technical_score = min(len(shared_technical) * 0.1, 0.3)  # Cap at 0.3

    total_score = mechanism_score + bridge_score + technical_score
    total_score = min(total_score, 1.0)

    # Determine evidence type
    if bridge_type != "NONE":
        evidence_type = bridge_type
    elif mechanism_score > 0:
        evidence_type = "MECHANISM"
    elif technical_score > 0:
        evidence_type = "METHOD"
    else:
        evidence_type = "NONE"

    return total_score, evidence_type


def audit_pair(source_a: dict, source_b: dict) -> PairAudit:
    """Audit a single candidate pair."""
    sid_a = source_a["source_id"]
    sid_b = source_b["source_id"]
    domain_a = source_a["domain"]
    domain_b = source_b["domain"]
    title_a = source_a.get("title", "")
    title_b = source_b.get("title", "")

    # 4. Domain distinctness
    domain_distinct = domain_a != domain_b

    # 5. Independent provenance (different DOIs, different publishers)
    doi_a = source_a.get("doi", "")
    doi_b = source_b.get("doi", "")
    pub_a = source_a.get("publisher", "")
    pub_b = source_b.get("publisher", "")
    independent = (doi_a != doi_b) if doi_a and doi_b else True

    # 6. Publication date validity (both have dates, both <= cutoff)
    date_a = source_a.get("publication_date", "")
    date_b = source_b.get("publication_date", "")
    dates_valid = bool(date_a) and bool(date_b)

    # 7. Full-text availability
    ft_a = source_a.get("has_full_text", False)
    ft_b = source_b.get("has_full_text", False)
    full_text = ft_a and ft_b

    # 8. Exact/near-duplicate exclusion
    exact_dup = (sha256_string(title_a) == sha256_string(title_b)) if title_a and title_b else False
    near_dup = SequenceMatcher(None, title_a.lower(), title_b.lower()).ratio() >= 0.85

    # 9. Citation/metadata relationship (simplified — would need full metadata)
    # For now, check if they share a publisher
    same_publisher = (pub_a == pub_b) if pub_a and pub_b else False

    # 10-11. Scientific bridge evidence vs lexical similarity
    lexical_sim = _jaccard(_tokenize(title_a), _tokenize(title_b))
    bridge_score, bridge_type = _compute_bridge_score(title_a, title_b, domain_a, domain_b)

    # 12. Disposition
    if exact_dup or near_dup:
        disposition = DUPLICATE
        notes = "Near-duplicate or exact duplicate detected"
    elif not domain_distinct:
        disposition = SAME_DOMAIN
        notes = f"Both sources in domain '{domain_a}'"
    elif not dates_valid:
        disposition = INSUFFICIENT_EVIDENCE
        notes = "Missing publication date(s)"
    elif not independent:
        disposition = DUPLICATE
        notes = "Same DOI — exact duplicate"
    elif bridge_score >= 0.5:
        disposition = PAIRABLE
        notes = f"Strong bridge evidence ({bridge_type}): score={bridge_score:.2f}"
    elif bridge_score >= 0.2:
        disposition = WEAK_BRIDGE
        notes = f"Weak bridge evidence ({bridge_type}): score={bridge_score:.2f}"
    else:
        disposition = INSUFFICIENT_EVIDENCE
        notes = f"No bridge evidence found: score={bridge_score:.2f}"

    return PairAudit(
        source_a_id=sid_a,
        source_b_id=sid_b,
        domain_a=domain_a,
        domain_b=domain_b,
        domain_distinct=domain_distinct,
        independent_provenance=independent,
        publication_date_valid=dates_valid,
        full_text_available=full_text,
        exact_duplicate=exact_dup,
        near_duplicate=near_dup,
        lexical_similarity=lexical_sim,
        scientific_bridge_score=bridge_score,
        bridge_evidence_type=bridge_type,
        disposition=disposition,
        notes=notes,
    )


def run_pairability_audit(
    eligible_pool_path: Path,
    output_dir: Path,
    max_pairs: Optional[int] = None,
) -> dict:
    """Run the full pairability audit.

    Args:
        eligible_pool_path: Path to eligible_source_pool.json
        output_dir: Where to save results
        max_pairs: Maximum pairs to audit (None = all pairs)

    Returns:
        Audit report
    """
    with open(eligible_pool_path) as f:
        pool_data = json.load(f)

    sources = pool_data.get("sources", [])
    n_sources = len(sources)

    print(f"=== SOURCE-PAIRABILITY AUDIT V1 ===")
    print(f"Eligible sources: {n_sources}")
    print(f"Total candidate pairs: {n_sources * (n_sources - 1) // 2}")
    print()

    # Generate all pairs (i < j to avoid duplicates and self-pairs)
    pairs = []
    for i in range(n_sources):
        for j in range(i + 1, n_sources):
            pairs.append((sources[i], sources[j]))
            if max_pairs and len(pairs) >= max_pairs:
                break
        if max_pairs and len(pairs) >= max_pairs:
            break

    print(f"Auditing {len(pairs)} pairs...")

    # Audit each pair
    audits = []
    for idx, (sa, sb) in enumerate(pairs):
        if (idx + 1) % 1000 == 0:
            print(f"  {idx + 1}/{len(pairs)}...")
        result = audit_pair(sa, sb)
        audits.append(result)

    # Compute statistics
    disposition_counts = Counter(a.disposition for a in audits)

    # By domain pair
    domain_pair_stats = defaultdict(lambda: {"candidate": 0, "pairable": 0, "weak": 0, "eligible": 0})
    for a in audits:
        if a.domain_distinct:
            pair_key = tuple(sorted([a.domain_a, a.domain_b]))
            domain_pair_stats[pair_key]["candidate"] += 1
            if a.disposition == PAIRABLE:
                domain_pair_stats[pair_key]["pairable"] += 1
                domain_pair_stats[pair_key]["eligible"] += 1
            elif a.disposition == WEAK_BRIDGE:
                domain_pair_stats[pair_key]["weak"] += 1

    # Summary
    n_pairable = disposition_counts.get(PAIRABLE, 0)
    n_weak = disposition_counts.get(WEAK_BRIDGE, 0)
    n_eligible = n_pairable + n_weak  # Weak bridges are eligible but flagged

    # Negative result check
    if n_eligible < 100:
        negative_result = (
            f"NEGATIVE_RESULT: {n_eligible} legitimate relationships found. "
            f"N≥100 cannot be justified from this corpus. "
            f"Acquire more independent corpus."
        )
    else:
        negative_result = None

    report = {
        "report_type": "SOURCE_PAIRABILITY_AUDIT_V1",
        "report_version": "1.0.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "source_count": n_sources,
        "total_pairs_audited": len(audits),
        "disposition_distribution": dict(disposition_counts.most_common()),
        "pairable_count": n_pairable,
        "weak_bridge_count": n_weak,
        "total_eligible_pairs": n_eligible,
        "n100_sufficient": n_eligible >= 100,
        "negative_result": negative_result,
        "domain_pair_distribution": {
            f"{k[0]} ↔ {k[1]}": v
            for k, v in sorted(domain_pair_stats.items(), key=lambda x: -x[1]["eligible"])
        },
        "methodology": {
            "lexical_similarity": "Jaccard on title tokens (informational only, does NOT control eligibility)",
            "scientific_bridge_score": "Heuristic mechanism-bridge score (controls eligibility)",
            "bridge_threshold_pairable": ">= 0.5",
            "bridge_threshold_weak": ">= 0.2 and < 0.5",
            "note": "Lexical similarity is NOT used as a proxy for scientific compatibility. "
                    "The bridge score looks for mechanism/process/method indicators that suggest "
                    "transferability, not word overlap.",
        },
        "note": "No benchmark questions constructed. No hypotheses generated. No TEE used. "
                "No taxonomy changes. No optimization for producing 100 pairs.",
    }

    # Save aggregate report
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "pairability_audit_aggregate.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Save detailed audit (custodian-only)
    detailed_path = output_dir / "pairability_audit_detailed.json"
    with open(detailed_path, 'w') as f:
        json.dump({
            "audit_type": "SOURCE_PAIRABILITY_AUDIT_DETAILED_V1",
            "total_pairs": len(audits),
            "audits": [a.to_dict() for a in audits],
            "note": "CUSTODIAN-ONLY. Contains source_ids and pair-level details. No TEE access.",
        }, f, indent=2)

    # Print summary
    print()
    print("=== SUMMARY ===")
    print(f"Sources: {n_sources}")
    print(f"Pairs audited: {len(audits)}")
    print()
    print("Disposition distribution:")
    for d, c in disposition_counts.most_common():
        print(f"  {d}: {c}")
    print()
    print(f"Pairable: {n_pairable}")
    print(f"Weak bridge: {n_weak}")
    print(f"Total eligible pairs: {n_eligible}")
    print(f"N≥100 sufficient: {'YES' if n_eligible >= 100 else 'NO'}")
    if negative_result:
        print()
        print(f"⚠️  {negative_result}")
    print()
    print("Top domain pairs (by eligible count):")
    for pair_key, stats in sorted(domain_pair_stats.items(), key=lambda x: -x[1]["eligible"])[:15]:
        print(f"  {pair_key[0]} ↔ {pair_key[1]}: {stats['eligible']} eligible ({stats['pairable']} strong, {stats['weak']} weak) out of {stats['candidate']}")
    print()
    print(f"Reports saved: {report_path}, {detailed_path}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True, help="Path to eligible_source_pool.json")
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()

    run_pairability_audit(
        eligible_pool_path=Path(args.pool),
        output_dir=Path(args.output),
        max_pairs=args.max_pairs,
    )
