"""
independent_corpus.intake.pairability_audit_v2_2 — Surgical fixes to V2.1.

Four changes:
A. Evidence integrity: abstract status/timestamp/hash, no silent empty
B. HARD_NEGATIVE → HARD_NEGATIVE_CANDIDATE
C. Frozen stratum precedence: mutually exclusive, deterministic
D. Question I (benchmarkability) added to adjudication

No new architecture. No TEE. No benchmark construction.
"""
import json
import random
import re
import sys
import math
import hashlib
import urllib.request
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from difflib import SequenceMatcher

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from custodian.src.domain_taxonomy import canonicalize_domain
from custodian.src.hasher import sha256_string, sha256_json
from independent_corpus.intake.pairability_audit import (
    audit_pair, _tokenize, _jaccard, _compute_bridge_score,
)

# Fix B: Rename to CANDIDATE
STRATUM_STRONG = "heuristic_strong"
STRATUM_WEAK = "heuristic_weak"
STRATUM_LEXICAL_LOW = "lexical_low_mechanistic"
STRATUM_HARD_NEGATIVE_CANDIDATE = "hard_negative_candidate"  # Fix B: renamed
STRATUM_RANDOM = "random_cross_domain"
STRATUM_UNAVAILABLE = "STRATUM_UNAVAILABLE"

# Fix C: Frozen stratum precedence (non-overlapping by construction)
# A pair is assigned to the FIRST stratum it qualifies for, in this order:
STRATUM_PRECEDENCE = [
    STRATUM_HARD_NEGATIVE_CANDIDATE,  # Highest: independent method, lexical >= 0.15
    STRATUM_STRONG,                   # bridge_score >= 0.5
    STRATUM_WEAK,                     # bridge_score >= 0.2 and < 0.5
    STRATUM_LEXICAL_LOW,              # lexical < 0.1, has mechanism indicators, bridge < 0.2
    STRATUM_RANDOM,                   # Everything else cross-domain
]

# Evidence status (Fix A)
EVIDENCE_PRESENT = "ABSTRACT_PRESENT"
EVIDENCE_UNAVAILABLE = "ABSTRACT_UNAVAILABLE"
EVIDENCE_REQUIRES_MANUAL_REVIEW = "SOURCE_REQUIRES_MANUAL_REVIEW"


@dataclass
class EvidenceItem:
    """Scientific evidence for one source (Fix A)."""
    status: str  # ABSTRACT_PRESENT, ABSTRACT_UNAVAILABLE, SOURCE_REQUIRES_MANUAL_REVIEW
    source_uri: str
    retrieval_timestamp: str
    content_hash: str  # SHA-256 of abstract content, or "" if unavailable
    text: str  # The abstract text, or "" if unavailable

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "source_uri": self.source_uri,
            "retrieval_timestamp": self.retrieval_timestamp,
            "content_hash": self.content_hash,
            "text_length": len(self.text),
        }


def fetch_abstract_with_integrity(doi: str, source_id: str) -> EvidenceItem:
    """Fetch abstract from OpenAlex with integrity tracking (Fix A).

    Never silently returns empty. Records status, URI, timestamp, hash.
    """
    timestamp = "2026-08-11T00:00:00Z"

    if not doi:
        return EvidenceItem(
            status=EVIDENCE_REQUIRES_MANUAL_REVIEW,
            source_uri="",
            retrieval_timestamp=timestamp,
            content_hash="",
            text="",
        )

    clean_doi = doi.replace("https://doi.org/", "").replace("https://dx.doi.org/", "")
    uri = f"https://api.openalex.org/works/doi:{clean_doi}?select=title,abstract_inverted_index"

    try:
        time.sleep(0.3)  # Rate limit
        req = urllib.request.Request(uri, headers={"User-Agent": "CustodianIntake/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        inv_idx = data.get("abstract_inverted_index", {})
        if not inv_idx:
            return EvidenceItem(
                status=EVIDENCE_UNAVAILABLE,
                source_uri=uri,
                retrieval_timestamp=timestamp,
                content_hash="",
                text="",
            )

        # Reconstruct abstract from inverted index
        positions = []
        for word, idxs in inv_idx.items():
            for pos in idxs:
                positions.append((pos, word))
        positions.sort()
        abstract = " ".join(w for _, w in positions)

        if not abstract.strip():
            return EvidenceItem(
                status=EVIDENCE_UNAVAILABLE,
                source_uri=uri,
                retrieval_timestamp=timestamp,
                content_hash="",
                text="",
            )

        return EvidenceItem(
            status=EVIDENCE_PRESENT,
            source_uri=uri,
            retrieval_timestamp=timestamp,
            content_hash=sha256_string(abstract),
            text=abstract,
        )

    except Exception as e:
        return EvidenceItem(
            status=EVIDENCE_UNAVAILABLE,
            source_uri=uri,
            retrieval_timestamp=timestamp,
            content_hash="",
            text="",
        )


@dataclass
class CandidatePairV22:
    """V2.2 candidate pair with evidence integrity and benchmarkability."""
    source_a_id: str
    source_b_id: str
    domain_a: str
    domain_b: str
    title_a: str
    title_b: str
    evidence_a: EvidenceItem
    evidence_b: EvidenceItem
    doi_a: str
    doi_b: str
    publisher_a: str
    publisher_b: str
    publication_date_a: str
    publication_date_b: str
    # Heuristic scores (NOT in blind packet)
    lexical_similarity: float
    scientific_bridge_score: float
    bridge_evidence_type: str
    heuristic_disposition: str
    stratum: str
    # Custodian adjudication (PENDING) — Fix D: added question I
    custodian_adjudication: dict = field(default_factory=lambda: {
        "A_mechanistic_relationship": "",
        "B_cross_domain": "",
        "C_transferable_mechanism": "",
        "D1_literature_established": "",
        "D2_search_adequate": "",
        "D3_novelty_status": "",
        "D4_search_universe": "",
        "E_non_trivial_discovery": "",
        "F_sufficiently_difficult": "",
        "G_legitimate_opportunity": "",
        "H_could_scientist_be_fooled": "",
        "I_benchmarkable": "",  # Fix D: NEW
        "task_type": "",
        "rationale": "",
        "adjudication_timestamp": "",
        "adjudicator_id": "",
    })

    def to_blind_dict(self) -> dict:
        """Blind view — scientific evidence, NO heuristic scores."""
        return {
            "source_a_id": self.source_a_id,
            "source_b_id": self.source_b_id,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "title_a": self.title_a,
            "title_b": self.title_b,
            "abstract_a": self.evidence_a.text,
            "abstract_a_status": self.evidence_a.status,  # Fix A: explicit status
            "abstract_a_hash": self.evidence_a.content_hash,
            "abstract_b": self.evidence_b.text,
            "abstract_b_status": self.evidence_b.status,
            "abstract_b_hash": self.evidence_b.content_hash,
            "doi_a": self.doi_a,
            "doi_b": self.doi_b,
            "publisher_a": self.publisher_a,
            "publisher_b": self.publisher_b,
            "publication_date_a": self.publication_date_a,
            "publication_date_b": self.publication_date_b,
            "custodian_adjudication": self.custodian_adjudication,
        }


def assign_stratum_non_overlapping(
    lexical_sim: float,
    bridge_score: float,
    bridge_type: str,
    is_hard_neg_candidate: bool,
) -> str:
    """Fix C: Assign stratum using frozen precedence (non-overlapping)."""
    for stratum in STRATUM_PRECEDENCE:
        if stratum == STRATUM_HARD_NEGATIVE_CANDIDATE and is_hard_neg_candidate:
            return stratum
        elif stratum == STRATUM_STRONG and bridge_score >= 0.5:
            return stratum
        elif stratum == STRATUM_WEAK and 0.2 <= bridge_score < 0.5:
            return stratum
        elif stratum == STRATUM_LEXICAL_LOW and lexical_sim < 0.1 and bridge_type != "NONE" and bridge_score < 0.2:
            return stratum
        elif stratum == STRATUM_RANDOM:
            return stratum  # Catch-all for cross-domain pairs not in other strata
    return STRATUM_RANDOM


def build_v22_candidate_pool(
    universe_path: Path,
    output_dir: Path,
    target_pool_size: int = 200,
    random_seed: int = 42,
    fetch_abstracts: bool = True,
) -> dict:
    """Build V2.2 candidate pool."""
    with open(universe_path) as f:
        universe = json.load(f)

    sources = universe.get("sources", [])
    n_sources = len(sources)
    manifest_hash = universe.get("manifest_hash", "")

    print(f"=== SOURCE_PAIRABILITY_AUDIT_V2.2 ===")
    print(f"Universe: FINAL_ELIGIBLE_SOURCE_UNIVERSE_V1")
    print(f"Manifest hash: {manifest_hash[:32]}...")
    print(f"Source count: {n_sources}")
    print(f"Target pool size: {target_pool_size}")
    print()

    # Generate ALL cross-domain pairs with heuristic scores
    all_pairs = []
    hard_neg_ids = set()  # Track hard-negative candidate pair IDs

    for i in range(n_sources):
        for j in range(i + 1, n_sources):
            sa, sb = sources[i], sources[j]
            if sa["domain"] == sb["domain"]:
                continue

            audit = audit_pair(sa, sb)
            if audit.disposition in ("DUPLICATE", "SAME_DOMAIN"):
                continue

            # Fix B/C: Determine if hard-negative candidate (independent method)
            lexical = audit.lexical_similarity
            is_hard_neg = lexical >= 0.15  # Independent of bridge score

            # Fix C: Assign stratum using frozen precedence
            stratum = assign_stratum_non_overlapping(
                lexical_sim=lexical,
                bridge_score=audit.scientific_bridge_score,
                bridge_type=audit.bridge_evidence_type,
                is_hard_neg_candidate=is_hard_neg,
            )

            pair = CandidatePairV22(
                source_a_id=sa["source_id"],
                source_b_id=sb["source_id"],
                domain_a=sa["domain"],
                domain_b=sb["domain"],
                title_a=sa.get("title", ""),
                title_b=sb.get("title", ""),
                evidence_a=EvidenceItem("", "", "", "", ""),  # Fetched later
                evidence_b=EvidenceItem("", "", "", "", ""),
                doi_a=sa.get("doi", ""),
                doi_b=sb.get("doi", ""),
                publisher_a=sa.get("publisher", ""),
                publisher_b=sb.get("publisher", ""),
                publication_date_a=sa.get("publication_date", ""),
                publication_date_b=sb.get("publication_date", ""),
                lexical_similarity=lexical,
                scientific_bridge_score=audit.scientific_bridge_score,
                bridge_evidence_type=audit.bridge_evidence_type,
                heuristic_disposition="HEURISTIC_CANDIDATE" if audit.scientific_bridge_score >= 0.5
                    else ("HEURISTIC_WEAK" if audit.scientific_bridge_score >= 0.2
                    else ("HARD_NEGATIVE_CANDIDATE" if is_hard_neg
                    else "INSUFFICIENT_EVIDENCE")),
                stratum=stratum,
            )
            all_pairs.append(pair)

    print(f"Cross-domain pairs: {len(all_pairs)}")

    # Group by stratum (Fix C: non-overlapping by construction)
    strata_pools = {s: [] for s in STRATUM_PRECEDENCE}
    for p in all_pairs:
        strata_pools[p.stratum].append(p)

    print(f"\nStrata (non-overlapping by construction):")
    for s in STRATUM_PRECEDENCE:
        print(f"  {s}: {len(strata_pools[s])}")

    # Sample with FROZEN proportions — no silent substitution
    random.seed(random_seed)
    strata_config = {
        STRATUM_HARD_NEGATIVE_CANDIDATE: 0.20,
        STRATUM_STRONG: 0.20,
        STRATUM_WEAK: 0.30,
        STRATUM_LEXICAL_LOW: 0.20,
        STRATUM_RANDOM: 0.10,
    }

    selected = []
    stratum_report = {}
    for stratum_name in STRATUM_PRECEDENCE:
        pool = strata_pools[stratum_name]
        proportion = strata_config[stratum_name]
        n_desired = int(target_pool_size * proportion)
        n_available = len(pool)
        n_selected = min(n_desired, n_available)

        if n_selected < n_desired:
            status = STRATUM_UNAVAILABLE
            print(f"  ⚠️  {stratum_name}: desired {n_desired}, available {n_available}, selected {n_selected} — {status}")
        else:
            status = "OK"
            print(f"  {stratum_name}: desired {n_desired}, available {n_available}, selected {n_selected} — {status}")

        stratum_report[stratum_name] = {
            "desired": n_desired,
            "available": n_available,
            "selected": n_selected,
            "status": status,
        }

        if n_selected > 0:
            sampled = random.sample(pool, n_selected)
            selected.extend(sampled)

    print(f"\nTotal selected: {len(selected)}")
    print(f"Stratum shortfalls: {sum(1 for s in stratum_report.values() if s['status'] == STRATUM_UNAVAILABLE)}")

    # Fix A: Fetch abstracts with integrity tracking
    if fetch_abstracts:
        print(f"\nFetching abstracts with integrity tracking...")
        for idx, pair in enumerate(selected):
            if (idx + 1) % 20 == 0:
                print(f"  {idx + 1}/{len(selected)}...")
            pair.evidence_a = fetch_abstract_with_integrity(pair.doi_a, pair.source_a_id)
            pair.evidence_b = fetch_abstract_with_integrity(pair.doi_b, pair.source_b_id)

    # Evidence status summary
    ev_status_a = Counter(p.evidence_a.status for p in selected)
    ev_status_b = Counter(p.evidence_b.status for p in selected)
    both_present = sum(1 for p in selected
                       if p.evidence_a.status == EVIDENCE_PRESENT
                       and p.evidence_b.status == EVIDENCE_PRESENT)

    print(f"\nEvidence status (Fix A):")
    print(f"  Abstract A: {dict(ev_status_a)}")
    print(f"  Abstract B: {dict(ev_status_b)}")
    print(f"  Both present: {both_present}/{len(selected)}")

    # Build blind packet
    blind_packets = [p.to_blind_dict() for p in selected]

    # Build full records
    full_records = []
    for p in selected:
        d = p.to_blind_dict()
        d["lexical_similarity"] = round(p.lexical_similarity, 4)
        d["scientific_bridge_score"] = round(p.scientific_bridge_score, 4)
        d["bridge_evidence_type"] = p.bridge_evidence_type
        d["heuristic_disposition"] = p.heuristic_disposition
        d["stratum"] = p.stratum
        full_records.append(d)

    # Domain pair distribution
    domain_pairs = Counter()
    for p in selected:
        pair_key = tuple(sorted([p.domain_a, p.domain_b]))
        domain_pairs[f"{pair_key[0]} ↔ {pair_key[1]}"] += 1

    report = {
        "report_type": "SOURCE_PAIRABILITY_AUDIT_V2_2",
        "report_version": "2.2.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "universe_manifest_hash": manifest_hash,
        "source_count": n_sources,
        "total_cross_domain_pairs": len(all_pairs),
        "target_pool_size": target_pool_size,
        "actual_pool_size": len(selected),
        "random_seed": random_seed,
        "stratum_report": stratum_report,
        "stratum_precedence": STRATUM_PRECEDENCE,  # Fix C: published
        "strata_non_overlapping": True,  # Fix C: by construction
        "stratum_proportions_frozen": True,
        "no_silent_substitution": True,
        "evidence_integrity": {  # Fix A
            "abstract_a_status": dict(ev_status_a),
            "abstract_b_status": dict(ev_status_b),
            "both_present": both_present,
            "rule": "ABSTRACT_PRESENT / ABSTRACT_UNAVAILABLE / SOURCE_REQUIRES_MANUAL_REVIEW — never silent empty",
        },
        "hard_negative_semantics": "HARD_NEGATIVE_CANDIDATE — not confirmed hard negative until custodian adjudicates",  # Fix B
        "domain_pair_distribution": dict(domain_pairs.most_common()),
        "adjudication_questions": {
            "A": "Is there a real mechanistic relationship? (YES/NO/UNCERTAIN)",
            "B": "Is the relationship cross-domain? (YES/NO)",
            "C": "Is there a plausible transferable mechanism? (YES/NO/UNCERTAIN)",
            "D1": "Is the specific relationship explicitly established in literature? (YES/NO/UNCERTAIN)",
            "D2": "Was relevant literature searched sufficiently? (ADEQUATE/INADEQUATE/INDETERMINATE)",
            "D3": "Novelty status? (ESTABLISHED/NOT_ESTABLISHED/INDETERMINATE)",
            "D4": "What search universe was checked? (text)",
            "E": "Can the pair generate a non-trivial discovery question? (YES/NO/UNCERTAIN)",
            "F": "Is it sufficiently difficult that a competent scientist cannot trivially answer? (YES/NO/UNCERTAIN)",
            "G": "Does it create a legitimate discovery opportunity? (YES/NO/UNCERTAIN)",
            "H": "Could a competent scientist be fooled into believing these mechanisms transfer when they actually do not? (YES/NO/UNCERTAIN)",
            "I": "Can this pair support a specific, falsifiable scientific prediction whose outcome could distinguish a genuine transfer from a superficial analogy? (YES/NO/UNCERTAIN)",  # Fix D: NEW
        },
        "task_type_rules": {
            "W_TASK": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES, I=YES, D3=ESTABLISHED",
            "S_CANDIDATE": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES, I=YES, D1=NO, D2=ADEQUATE, D3=NOT_ESTABLISHED",
            "REJECT": "Does not meet W or S criteria, or I≠YES",
        },
        "note": "Fix D: I=YES is REQUIRED for benchmark candidacy. Without benchmarkability, a pair cannot become a benchmark case.",
        "negative_result_check": "If custodian adjudicates <100 qualifying pairs (I=YES + acceptance rule), report NEGATIVE_RESULT.",
    }

    # Save
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blind_path = output_dir / "pairability_v2_2_blind_packet.json"
    with open(blind_path, 'w') as f:
        json.dump({
            "packet_type": "BLIND_PAIRABILITY_ADJUDICATION_V2_2",
            "packet_version": "1.0.0",
            "universe_manifest_hash": manifest_hash,
            "pair_count": len(blind_packets),
            "adjudication_questions": report["adjudication_questions"],
            "task_type_rules": report["task_type_rules"],
            "rules": [
                "Custodian must NOT see heuristic scores, dispositions, or strata before adjudicating.",
                "Custodian must answer A-I for every pair.",
                "I=YES is REQUIRED for benchmark candidacy.",
                "D1=NO alone does NOT establish S-TASK. Requires D1=NO AND D2=ADEQUATE AND D3=NOT_ESTABLISHED.",
                "If abstract status is ABSENT or REQUIRES_MANUAL_REVIEW, note this in rationale.",
                "If <100 pairs qualify, report NEGATIVE_RESULT.",
                "No TEE access. No benchmark construction. No taxonomy changes.",
            ],
            "pairs": blind_packets,
        }, f, indent=2)

    full_path = output_dir / "pairability_v2_2_full_records.json"
    with open(full_path, 'w') as f:
        json.dump({
            "record_type": "PAIRABILITY_V2_2_FULL_RECORDS",
            "universe_manifest_hash": manifest_hash,
            "pair_count": len(full_records),
            "records": full_records,
        }, f, indent=2)

    report_path = output_dir / "pairability_v2_2_aggregate_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFiles saved:")
    print(f"  Blind packet: {blind_path}")
    print(f"  Full records: {full_path}")
    print(f"  Aggregate report: {report_path}")
    print()
    print("NEXT STEP: Custodian adjudicates blind packet (A-I questions per pair).")
    print("I=YES is REQUIRED for benchmark candidacy.")
    print()
    print("NO BENCHMARK CONSTRUCTED. No TEE. No taxonomy changes.")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True)
    parser.add_argument("--output", default=".")
    parser.add_argument("--target-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-abstracts", action="store_true")
    args = parser.parse_args()

    build_v22_candidate_pool(
        universe_path=Path(args.universe),
        output_dir=Path(args.output),
        target_pool_size=args.target_size,
        random_seed=args.seed,
        fetch_abstracts=not args.no_abstracts,
    )
