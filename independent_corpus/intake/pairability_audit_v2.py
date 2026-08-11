"""
independent_corpus.intake.pairability_audit_v2 — Source-pairability audit V2.

Key changes from V1:
1. Reclassifies V1's "PAIRABLE" as HEURISTIC_CANDIDATE (not scientific bridge)
2. Separates candidate generation from scientific adjudication
3. Builds blind semantic-adjudication packets for custodian
4. Adds W-TASK vs S-TASK classification
5. Adds stratified candidate pool (strong/weak/lexical-low/hard-negatives/random)
6. Produces negative result artifact if insufficient

The heuristic generates candidates. The custodian decides scientific eligibility.
"""
import json
import random
import sys
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from custodian.src.domain_taxonomy import canonicalize_domain
from custodian.src.hasher import sha256_string, sha256_json
from independent_corpus.intake.pairability_audit import (
    audit_pair,
    _tokenize,
    _jaccard,
    _compute_bridge_score,
)


# V2 dispositions (renamed from V1)
HEURISTIC_CANDIDATE = "HEURISTIC_CANDIDATE"  # Was PAIRABLE in V1
HEURISTIC_WEAK = "HEURISTIC_WEAK"  # Was WEAK_BRIDGE in V1
DUPLICATE = "DUPLICATE"
SAME_DOMAIN = "SAME_DOMAIN"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
OUTSIDE_SCOPE = "OUTSIDE_SCOPE"

# Task types
W_TASK = "W-TASK"  # Rediscovery: can TEE find a non-obvious relationship?
S_TASK = "S-TASK"  # World-novel: can TEE generate a hypothesis not in literature?

# Strata for candidate pool
STRATUM_STRONG = "heuristic_strong"      # bridge_score >= 0.5
STRATUM_WEAK = "heuristic_weak"          # bridge_score >= 0.2 and < 0.5
STRATUM_LEXICAL_LOW = "lexical_low_mechanistic"  # low lexical, has mechanism indicators
STRATUM_HARD_NEGATIVE = "hard_negative"  # high lexical, no bridge (seductive false bridges)
STRATUM_RANDOM = "random_cross_domain"   # random cross-domain pairs


@dataclass
class CandidatePair:
    """A candidate pair for custodian adjudication."""
    source_a_id: str
    source_b_id: str
    domain_a: str
    domain_b: str
    title_a: str
    title_b: str
    doi_a: str
    doi_b: str
    publisher_a: str
    publisher_b: str
    publication_date_a: str
    publication_date_b: str
    # Heuristic scores (informational only)
    lexical_similarity: float
    scientific_bridge_score: float
    bridge_evidence_type: str
    heuristic_disposition: str  # HEURISTIC_CANDIDATE, HEURISTIC_WEAK, etc.
    stratum: str  # Which stratum this pair belongs to
    # Custodian adjudication (PENDING — custodian fills in)
    custodian_adjudication: dict = field(default_factory=lambda: {
        "A_mechanistic_relationship": "",  # YES/NO/UNCERTAIN
        "B_cross_domain": "",              # YES/NO
        "C_transferable_mechanism": "",    # YES/NO/UNCERTAIN
        "D_already_established": "",       # YES/NO/UNCERTAIN
        "E_non_trivial_discovery": "",     # YES/NO/UNCERTAIN
        "F_sufficiently_difficult": "",    # YES/NO/UNCERTAIN
        "G_legitimate_opportunity": "",    # YES/NO/UNCERTAIN
        "task_type": "",                   # W-TASK, S-TASK, or REJECT
        "rationale": "",
        "adjudication_timestamp": "",
        "adjudicator_id": "",
    })

    def to_blind_dict(self) -> dict:
        """Blind view for custodian — NO heuristic scores or disposition."""
        return {
            "source_a_id": self.source_a_id,
            "source_b_id": self.source_b_id,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "title_a": self.title_a,
            "title_b": self.title_b,
            "doi_a": self.doi_a,
            "doi_b": self.doi_b,
            "publisher_a": self.publisher_a,
            "publisher_b": self.publisher_b,
            "publication_date_a": self.publication_date_a,
            "publication_date_b": self.publication_date_b,
            "custodian_adjudication": self.custodian_adjudication,
        }

    def to_full_dict(self) -> dict:
        """Full view (custodian-only after adjudication)."""
        return {
            "source_a_id": self.source_a_id,
            "source_b_id": self.source_b_id,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "title_a": self.title_a,
            "title_b": self.title_b,
            "doi_a": self.doi_a,
            "doi_b": self.doi_b,
            "lexical_similarity": round(self.lexical_similarity, 4),
            "scientific_bridge_score": round(self.scientific_bridge_score, 4),
            "bridge_evidence_type": self.bridge_evidence_type,
            "heuristic_disposition": self.heuristic_disposition,
            "stratum": self.stratum,
            "custodian_adjudication": self.custodian_adjudication,
        }


def build_stratified_candidate_pool(
    eligible_pool_path: Path,
    output_dir: Path,
    target_pool_size: int = 200,
    random_seed: int = 42,
) -> dict:
    """Build a stratified candidate pool from the eligible sources.

    Strata (frozen proportions):
      20% heuristic_strong (bridge_score >= 0.5)
      30% heuristic_weak (bridge_score >= 0.2 and < 0.5)
      20% lexical_low_mechanistic (low lexical, has mechanism indicators)
      20% hard_negative (high lexical, no bridge — seductive false bridges)
      10% random_cross_domain

    The custodian decides final proportions. These are DEFAULTS.
    """
    with open(eligible_pool_path) as f:
        pool_data = json.load(f)

    sources = pool_data.get("sources", [])
    n_sources = len(sources)

    print(f"=== SOURCE_PAIRABILITY_AUDIT_V2 ===")
    print(f"Eligible sources: {n_sources}")
    print(f"Target candidate pool size: {target_pool_size}")
    print()

    # Generate ALL cross-domain pairs and compute scores
    all_pairs = []
    for i in range(n_sources):
        for j in range(i + 1, n_sources):
            sa, sb = sources[i], sources[j]
            if sa["domain"] == sb["domain"]:
                continue  # Skip same-domain

            audit = audit_pair(sa, sb)
            if audit.disposition in ("DUPLICATE", "SAME_DOMAIN"):
                continue

            pair = CandidatePair(
                source_a_id=sa["source_id"],
                source_b_id=sb["source_id"],
                domain_a=sa["domain"],
                domain_b=sb["domain"],
                title_a=sa.get("title", ""),
                title_b=sb.get("title", ""),
                doi_a=sa.get("doi", ""),
                doi_b=sb.get("doi", ""),
                publisher_a=sa.get("publisher", ""),
                publisher_b=sb.get("publisher", ""),
                publication_date_a=sa.get("publication_date", ""),
                publication_date_b=sb.get("publication_date", ""),
                lexical_similarity=audit.lexical_similarity,
                scientific_bridge_score=audit.scientific_bridge_score,
                bridge_evidence_type=audit.bridge_evidence_type,
                heuristic_disposition=HEURISTIC_CANDIDATE if audit.scientific_bridge_score >= 0.5
                    else (HEURISTIC_WEAK if audit.scientific_bridge_score >= 0.2
                    else INSUFFICIENT_EVIDENCE),
                stratum="",  # Assigned below
            )
            all_pairs.append(pair)

    print(f"Cross-domain pairs (non-duplicate): {len(all_pairs)}")

    # Classify into strata
    strong = [p for p in all_pairs if p.scientific_bridge_score >= 0.5]
    weak = [p for p in all_pairs if 0.2 <= p.scientific_bridge_score < 0.5]
    lexical_low = [p for p in all_pairs if p.lexical_similarity < 0.1
                   and p.bridge_evidence_type != "NONE"
                   and p.scientific_bridge_score < 0.2]
    hard_neg = [p for p in all_pairs if p.lexical_similarity >= 0.2
                and p.scientific_bridge_score < 0.2]
    random_pool = [p for p in all_pairs if p not in strong and p not in weak
                   and p not in lexical_low and p not in hard_neg]

    print(f"  heuristic_strong: {len(strong)}")
    print(f"  heuristic_weak: {len(weak)}")
    print(f"  lexical_low_mechanistic: {len(lexical_low)}")
    print(f"  hard_negative: {len(hard_neg)}")
    print(f"  random_cross_domain: {len(random_pool)}")
    print()

    # Sample from each stratum
    random.seed(random_seed)
    strata = {
        STRATUM_STRONG: (strong, 0.20),
        STRATUM_WEAK: (weak, 0.30),
        STRATUM_LEXICAL_LOW: (lexical_low, 0.20),
        STRATUM_HARD_NEGATIVE: (hard_neg, 0.20),
        STRATUM_RANDOM: (random_pool, 0.10),
    }

    selected = []
    for stratum_name, (pool, proportion) in strata.items():
        n_select = min(int(target_pool_size * proportion), len(pool))
        if n_select > 0:
            sampled = random.sample(pool, n_select)
            for p in sampled:
                p.stratum = stratum_name
            selected.extend(sampled)
            print(f"  Selected {n_select} from {stratum_name} (pool: {len(pool)})")

    print(f"\nTotal selected: {len(selected)}")

    # Build blind adjudication packets
    blind_packets = [p.to_blind_dict() for p in selected]

    # Build full record (custodian-only)
    full_records = [p.to_full_dict() for p in selected]

    # Domain pair distribution
    domain_pairs = Counter()
    for p in selected:
        pair_key = tuple(sorted([p.domain_a, p.domain_b]))
        domain_pairs[f"{pair_key[0]} ↔ {pair_key[1]}"] += 1

    # Stratum distribution
    stratum_counts = Counter(p.stratum for p in selected)

    report = {
        "report_type": "SOURCE_PAIRABILITY_AUDIT_V2",
        "report_version": "2.0.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "source_count": n_sources,
        "total_cross_domain_pairs": len(all_pairs),
        "target_pool_size": target_pool_size,
        "actual_pool_size": len(selected),
        "random_seed": random_seed,
        "stratum_distribution": dict(stratum_counts.most_common()),
        "stratum_proportions": {
            STRATUM_STRONG: "20%",
            STRATUM_WEAK: "30%",
            STRATUM_LEXICAL_LOW: "20%",
            STRATUM_HARD_NEGATIVE: "20%",
            STRATUM_RANDOM: "10%",
        },
        "domain_pair_distribution": dict(domain_pairs.most_common()),
        "key_change_from_v1": (
            "V1's 'PAIRABLE' disposition is reclassified as 'HEURISTIC_CANDIDATE'. "
            "The heuristic generates candidates; it does NOT decide scientific eligibility. "
            "Custodian must independently adjudicate each pair using the A-G questions."
        ),
        "adjudication_questions": {
            "A": "Is there a real mechanistic relationship? (YES/NO/UNCERTAIN)",
            "B": "Is the relationship cross-domain? (YES/NO)",
            "C": "Is there a plausible transferable mechanism? (YES/NO/UNCERTAIN)",
            "D": "Is the relationship already explicitly established? (YES/NO/UNCERTAIN)",
            "E": "Can the pair generate a non-trivial discovery question? (YES/NO/UNCERTAIN)",
            "F": "Is it sufficiently difficult that a competent scientist cannot trivially answer? (YES/NO/UNCERTAIN)",
            "G": "Does it create a legitimate discovery opportunity? (YES/NO/UNCERTAIN)",
        },
        "task_types": {
            "W-TASK": "Can TEE discover a non-obvious relationship? (includes retrospective)",
            "S-TASK": "Can TEE generate a world-novel hypothesis not in literature?",
            "REJECT": "Pair does not qualify for benchmark",
        },
        "acceptance_rule": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES → candidate benchmark pair",
        "note": "D=YES does not disqualify, but classifies as W-TASK (rediscovery) not S-TASK (world-novel).",
        "negative_result_check": "If custodian adjudicates <100 qualifying pairs, report NEGATIVE_RESULT.",
    }

    # Save
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Blind adjudication packet (for custodian)
    blind_path = output_dir / "pairability_v2_blind_adjudication_packet.json"
    with open(blind_path, 'w') as f:
        json.dump({
            "packet_type": "BLIND_PAIRABILITY_ADJUDICATION_V2",
            "packet_version": "1.0.0",
            "pair_count": len(blind_packets),
            "adjudication_questions": report["adjudication_questions"],
            "task_types": report["task_types"],
            "acceptance_rule": report["acceptance_rule"],
            "rules": [
                "Custodian must NOT see heuristic scores or dispositions before adjudicating.",
                "Custodian must answer A-G for every pair.",
                "Only A=YES, B=YES, C=YES, E=YES, F=YES, G=YES pairs become candidates.",
                "D=YES classifies as W-TASK (rediscovery), not S-TASK (world-novel).",
                "If <100 pairs qualify, report NEGATIVE_RESULT.",
                "No TEE access. No benchmark construction. No taxonomy changes.",
            ],
            "pairs": blind_packets,
        }, f, indent=2)

    # Full record (custodian-only, for after adjudication)
    full_path = output_dir / "pairability_v2_full_records.json"
    with open(full_path, 'w') as f:
        json.dump({
            "record_type": "PAIRABILITY_V2_FULL_RECORDS",
            "pair_count": len(full_records),
            "records": full_records,
            "note": "CUSTODIAN-ONLY. Contains heuristic scores. Do NOT show to TEE.",
        }, f, indent=2)

    # Aggregate report
    report_path = output_dir / "pairability_v2_aggregate_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFiles saved:")
    print(f"  Blind packet: {blind_path}")
    print(f"  Full records: {full_path}")
    print(f"  Aggregate report: {report_path}")
    print()
    print("NEXT STEP: Custodian adjudicates the blind packet (A-G questions per pair).")
    print("Then reveal heuristic scores and compute agreement.")
    print("Then decide if >=100 pairs qualify for benchmark construction.")
    print()
    print("NO BENCHMARK CONSTRUCTED. No TEE. No taxonomy changes.")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--output", default=".")
    parser.add_argument("--target-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    build_stratified_candidate_pool(
        eligible_pool_path=Path(args.pool),
        output_dir=Path(args.output),
        target_pool_size=args.target_size,
        random_seed=args.seed,
    )
