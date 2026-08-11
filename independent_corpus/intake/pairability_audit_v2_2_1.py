"""
independent_corpus.intake.pairability_audit_v2_2_1 — Surgical fix to V2.2.

V2.2 had two critical defects:
1. Hard-negative precedence overrode scientific strata (lexical >= 0.15 captured all such pairs)
2. Retrieval timestamp was hardcoded, not actual

V2.2.1 fixes:
1. MAIN STRATA restored: STRONG > WEAK > LEXICAL_LOW > RANDOM
2. HARD_NEGATIVE_CANDIDATE is an independent OVERLAY (not part of main precedence)
3. No pair appears in two sampled strata (enforced by ID tracking)
4. Real UTC retrieval timestamps (datetime.now(timezone.utc))
5. Abstracts fetched once per unique source (cached)
6. Missing evidence = ABSTRACT_UNAVAILABLE (visible, never silent)
7. Invariant tests prove all properties

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
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

# Fix 1: MAIN STRATA (restored — hard-negative is NOT in this list)
STRATUM_STRONG = "heuristic_strong"
STRATUM_WEAK = "heuristic_weak"
STRATUM_LEXICAL_LOW = "lexical_low_mechanistic"
STRATUM_RANDOM = "random_cross_domain"

# Fix 2: HARD_NEGATIVE_CANDIDATE is an independent OVERLAY
STRATUM_HARD_NEG_OVERLAY = "hard_negative_candidate_overlay"

STRATUM_UNAVAILABLE = "STRATUM_UNAVAILABLE"

# Fix 1: Main stratum precedence (hard-negative NOT included)
MAIN_STRATUM_PRECEDENCE = [
    STRATUM_STRONG,      # bridge_score >= 0.5
    STRATUM_WEAK,        # bridge_score >= 0.2 and < 0.5
    STRATUM_LEXICAL_LOW, # lexical < 0.1, has mechanism indicators, bridge < 0.2
    STRATUM_RANDOM,      # Everything else cross-domain
]

# Evidence status
EVIDENCE_PRESENT = "ABSTRACT_PRESENT"
EVIDENCE_UNAVAILABLE = "ABSTRACT_UNAVAILABLE"
EVIDENCE_REQUIRES_MANUAL_REVIEW = "SOURCE_REQUIRES_MANUAL_REVIEW"


@dataclass
class EvidenceItem:
    """Fix 4: Real retrieval timestamp. Fix 6: Explicit status."""
    status: str
    source_uri: str
    retrieval_timestamp: str  # Fix 4: actual UTC, not hardcoded
    content_hash: str
    text: str

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "source_uri": self.source_uri,
            "retrieval_timestamp": self.retrieval_timestamp,
            "content_hash": self.content_hash,
            "text_length": len(self.text),
        }


# Fix 5: Cache abstracts per unique source
_abstract_cache: Dict[str, EvidenceItem] = {}


def fetch_abstract_cached(doi: str) -> EvidenceItem:
    """Fix 5: Fetch abstract once per unique source. Cache result."""
    if doi in _abstract_cache:
        return _abstract_cache[doi]

    # Fix 4: Real retrieval timestamp
    retrieval_ts = datetime.now(timezone.utc).isoformat()

    if not doi:
        result = EvidenceItem(
            status=EVIDENCE_REQUIRES_MANUAL_REVIEW,
            source_uri="",
            retrieval_timestamp=retrieval_ts,
            content_hash="",
            text="",
        )
        _abstract_cache[doi] = result
        return result

    clean_doi = doi.replace("https://doi.org/", "").replace("https://dx.doi.org/", "")
    uri = f"https://api.openalex.org/works/doi:{clean_doi}?select=title,abstract_inverted_index"

    try:
        time.sleep(0.3)
        req = urllib.request.Request(uri, headers={"User-Agent": "CustodianIntake/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        inv_idx = data.get("abstract_inverted_index", {})
        if not inv_idx:
            result = EvidenceItem(
                status=EVIDENCE_UNAVAILABLE,
                source_uri=uri,
                retrieval_timestamp=retrieval_ts,
                content_hash="",
                text="",
            )
            _abstract_cache[doi] = result
            return result

        positions = []
        for word, idxs in inv_idx.items():
            for pos in idxs:
                positions.append((pos, word))
        positions.sort()
        abstract = " ".join(w for _, w in positions)

        if not abstract.strip():
            result = EvidenceItem(
                status=EVIDENCE_UNAVAILABLE,
                source_uri=uri,
                retrieval_timestamp=retrieval_ts,
                content_hash="",
                text="",
            )
            _abstract_cache[doi] = result
            return result

        result = EvidenceItem(
            status=EVIDENCE_PRESENT,
            source_uri=uri,
            retrieval_timestamp=retrieval_ts,
            content_hash=sha256_string(abstract),
            text=abstract,
        )
        _abstract_cache[doi] = result
        return result

    except Exception:
        result = EvidenceItem(
            status=EVIDENCE_UNAVAILABLE,
            source_uri=uri,
            retrieval_timestamp=retrieval_ts,
            content_hash="",
            text="",
        )
        _abstract_cache[doi] = result
        return result


def assign_main_stratum(lexical_sim: float, bridge_score: float, bridge_type: str) -> str:
    """Fix 1: Assign MAIN stratum (hard-negative NOT in this function)."""
    for stratum in MAIN_STRATUM_PRECEDENCE:
        if stratum == STRATUM_STRONG and bridge_score >= 0.5:
            return stratum
        elif stratum == STRATUM_WEAK and 0.2 <= bridge_score < 0.5:
            return stratum
        elif stratum == STRATUM_LEXICAL_LOW and lexical_sim < 0.1 and bridge_type != "NONE" and bridge_score < 0.2:
            return stratum
        elif stratum == STRATUM_RANDOM:
            return stratum
    return STRATUM_RANDOM


def is_hard_negative_candidate(lexical_sim: float) -> bool:
    """Fix 2: Independent hard-negative overlay (NOT a scientific classification)."""
    return lexical_sim >= 0.15


@dataclass
class CandidatePairV221:
    """V2.2.1 candidate pair."""
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
    lexical_similarity: float
    scientific_bridge_score: float
    bridge_evidence_type: str
    main_stratum: str  # Fix 1: MAIN stratum (STRONG/WEAK/LEX_LOW/RANDOM)
    is_hard_neg_candidate: bool  # Fix 2: overlay flag (independent)
    sampled_stratum: str  # Which stratum this pair was actually sampled INTO

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
        "I_benchmarkable": "",
        "task_type": "",
        "rationale": "",
        "adjudication_timestamp": "",
        "adjudicator_id": "",
    })

    def to_blind_dict(self) -> dict:
        return {
            "source_a_id": self.source_a_id,
            "source_b_id": self.source_b_id,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "title_a": self.title_a,
            "title_b": self.title_b,
            "abstract_a": self.evidence_a.text,
            "abstract_a_status": self.evidence_a.status,
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


def build_v221_candidate_pool(
    universe_path: Path,
    output_dir: Path,
    target_pool_size: int = 200,
    random_seed: int = 42,
    fetch_abstracts: bool = True,
) -> dict:
    """Build V2.2.1 candidate pool."""
    with open(universe_path) as f:
        universe = json.load(f)

    sources = universe.get("sources", [])
    n_sources = len(sources)
    manifest_hash = universe.get("manifest_hash", "")

    print(f"=== SOURCE_PAIRABILITY_AUDIT_V2.2.1 ===")
    print(f"Universe hash: {manifest_hash[:32]}...")
    print(f"Sources: {n_sources}")
    print(f"Target: {target_pool_size}")
    print()

    # Generate ALL cross-domain pairs
    all_pairs = []
    for i in range(n_sources):
        for j in range(i + 1, n_sources):
            sa, sb = sources[i], sources[j]
            if sa["domain"] == sb["domain"]:
                continue
            audit = audit_pair(sa, sb)
            if audit.disposition in ("DUPLICATE", "SAME_DOMAIN"):
                continue

            lexical = audit.lexical_similarity
            bridge = audit.scientific_bridge_score

            # Fix 1: Assign MAIN stratum (hard-negative NOT included)
            main_stratum = assign_main_stratum(lexical, bridge, audit.bridge_evidence_type)
            # Fix 2: Independent hard-negative overlay
            is_hn = is_hard_negative_candidate(lexical)

            pair = CandidatePairV221(
                source_a_id=sa["source_id"],
                source_b_id=sb["source_id"],
                domain_a=sa["domain"],
                domain_b=sb["domain"],
                title_a=sa.get("title", ""),
                title_b=sb.get("title", ""),
                evidence_a=EvidenceItem("", "", "", "", ""),
                evidence_b=EvidenceItem("", "", "", "", ""),
                doi_a=sa.get("doi", ""),
                doi_b=sb.get("doi", ""),
                publisher_a=sa.get("publisher", ""),
                publisher_b=sb.get("publisher", ""),
                publication_date_a=sa.get("publication_date", ""),
                publication_date_b=sb.get("publication_date", ""),
                lexical_similarity=lexical,
                scientific_bridge_score=bridge,
                bridge_evidence_type=audit.bridge_evidence_type,
                main_stratum=main_stratum,
                is_hard_neg_candidate=is_hn,
                sampled_stratum="",  # Assigned during sampling
            )
            all_pairs.append(pair)

    print(f"Cross-domain pairs: {len(all_pairs)}")

    # Fix 2: Separate hard-negative overlay pool
    hn_pool = [p for p in all_pairs if p.is_hard_neg_candidate]
    main_pools = {s: [] for s in MAIN_STRATUM_PRECEDENCE}
    for p in all_pairs:
        main_pools[p.main_stratum].append(p)

    print(f"\nMain strata (non-overlapping):")
    for s in MAIN_STRATUM_PRECEDENCE:
        print(f"  {s}: {len(main_pools[s])}")
    print(f"  Hard-negative overlay: {len(hn_pool)} (independent, may overlap with main)")

    # Fix 3: Sample independently — no pair in two sampled strata
    random.seed(random_seed)
    used_pair_ids: Set[Tuple[str, str]] = set()

    # Sample hard-negative overlay first (40 desired)
    hn_desired = int(target_pool_size * 0.20)
    hn_available = len(hn_pool)
    hn_selected = min(hn_desired, hn_available)
    hn_sampled = random.sample(hn_pool, hn_selected) if hn_selected > 0 else []
    for p in hn_sampled:
        p.sampled_stratum = STRATUM_HARD_NEG_OVERLAY
        used_pair_ids.add((p.source_a_id, p.source_b_id))

    # Sample main strata (remaining 160)
    main_config = {
        STRATUM_STRONG: 0.25,    # 40 of 160
        STRATUM_WEAK: 0.375,     # 60 of 160
        STRATUM_LEXICAL_LOW: 0.25, # 40 of 160
        STRATUM_RANDOM: 0.125,   # 20 of 160
    }

    main_selected = []
    stratum_report = {}

    # Hard-negative report
    stratum_report[STRATUM_HARD_NEG_OVERLAY] = {
        "desired": hn_desired,
        "available": hn_available,
        "selected": hn_selected,
        "status": "OK" if hn_selected >= hn_desired else STRATUM_UNAVAILABLE,
    }
    hn_status = stratum_report[STRATUM_HARD_NEG_OVERLAY]["status"]
    print(f"\n  {STRATUM_HARD_NEG_OVERLAY}: desired {hn_desired}, available {hn_available}, selected {hn_selected} — {hn_status}")

    remaining_target = target_pool_size - hn_selected

    for stratum_name in MAIN_STRATUM_PRECEDENCE:
        pool = main_pools[stratum_name]
        # Exclude pairs already sampled as hard-negative
        available = [p for p in pool if (p.source_a_id, p.source_b_id) not in used_pair_ids]
        proportion = main_config[stratum_name]
        n_desired = int(remaining_target * proportion)
        n_available = len(available)
        n_selected = min(n_desired, n_available)

        status = "OK" if n_selected >= n_desired else STRATUM_UNAVAILABLE
        stratum_report[stratum_name] = {
            "desired": n_desired,
            "available": n_available,
            "selected": n_selected,
            "status": status,
        }
        print(f"  {stratum_name}: desired {n_desired}, available {n_available}, selected {n_selected} — {status}")

        if n_selected > 0:
            sampled = random.sample(available, n_selected)
            for p in sampled:
                p.sampled_stratum = stratum_name
                used_pair_ids.add((p.source_a_id, p.source_b_id))
            main_selected.extend(sampled)

    selected = hn_sampled + main_selected

    print(f"\nTotal selected: {len(selected)}")
    print(f"Stratum shortfalls: {sum(1 for s in stratum_report.values() if s['status'] == STRATUM_UNAVAILABLE)}")

    # Fix 3 verification: no pair in two strata
    assert len(used_pair_ids) == len(selected), "PAIR IN TWO STRATA — INVARIANT VIOLATED"

    # Fix 5: Fetch abstracts once per unique source
    if fetch_abstracts:
        print(f"\nFetching abstracts (cached per source)...")
        unique_dois = set()
        for p in selected:
            if p.doi_a: unique_dois.add(p.doi_a)
            if p.doi_b: unique_dois.add(p.doi_b)
        print(f"  Unique DOIs to fetch: {len(unique_dois)}")

        for idx, doi in enumerate(sorted(unique_dois)):
            if (idx + 1) % 20 == 0:
                print(f"  {idx + 1}/{len(unique_dois)}...")
            fetch_abstract_cached(doi)

        # Assign cached evidence to pairs
        for p in selected:
            p.evidence_a = _abstract_cache.get(p.doi_a, EvidenceItem(EVIDENCE_REQUIRES_MANUAL_REVIEW, "", "", "", ""))
            p.evidence_b = _abstract_cache.get(p.doi_b, EvidenceItem(EVIDENCE_REQUIRES_MANUAL_REVIEW, "", "", "", ""))

    # Evidence status summary
    ev_a = Counter(p.evidence_a.status for p in selected)
    ev_b = Counter(p.evidence_b.status for p in selected)
    both = sum(1 for p in selected if p.evidence_a.status == EVIDENCE_PRESENT and p.evidence_b.status == EVIDENCE_PRESENT)
    print(f"\nEvidence status:")
    print(f"  Abstract A: {dict(ev_a)}")
    print(f"  Abstract B: {dict(ev_b)}")
    print(f"  Both present: {both}/{len(selected)}")

    # Build blind packet
    blind_packets = [p.to_blind_dict() for p in selected]

    # Build full records
    full_records = []
    for p in selected:
        d = p.to_blind_dict()
        d["lexical_similarity"] = round(p.lexical_similarity, 4)
        d["scientific_bridge_score"] = round(p.scientific_bridge_score, 4)
        d["bridge_evidence_type"] = p.bridge_evidence_type
        d["main_stratum"] = p.main_stratum
        d["is_hard_neg_candidate"] = p.is_hard_neg_candidate
        d["sampled_stratum"] = p.sampled_stratum
        full_records.append(d)

    # Domain pair distribution
    domain_pairs = Counter()
    for p in selected:
        pair_key = tuple(sorted([p.domain_a, p.domain_b]))
        domain_pairs[f"{pair_key[0]} ↔ {pair_key[1]}"] += 1

    # Sampled stratum distribution
    sampled_strata = Counter(p.sampled_stratum for p in selected)

    report = {
        "report_type": "SOURCE_PAIRABILITY_AUDIT_V2_2_1",
        "report_version": "2.2.1",
        "universe_manifest_hash": manifest_hash,
        "source_count": n_sources,
        "total_cross_domain_pairs": len(all_pairs),
        "actual_pool_size": len(selected),
        "random_seed": random_seed,
        "stratum_report": stratum_report,
        "sampled_stratum_distribution": dict(sampled_strata),
        "main_stratum_precedence": MAIN_STRATUM_PRECEDENCE,
        "hard_negative_is_overlay": True,
        "hard_negative_not_in_main_precedence": True,
        "no_pair_in_two_strata": True,
        "evidence_status": {
            "abstract_a": dict(ev_a),
            "abstract_b": dict(ev_b),
            "both_present": both,
        },
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
            "I": "Can this pair support a specific, falsifiable scientific prediction whose outcome could distinguish a genuine transfer from a superficial analogy? (YES/NO/UNCERTAIN)",
        },
        "task_type_rules": {
            "W_TASK": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES, I=YES, D3=ESTABLISHED",
            "S_CANDIDATE": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES, I=YES, D1=NO, D2=ADEQUATE, D3=NOT_ESTABLISHED",
            "REJECT": "Does not meet W or S criteria, or I≠YES",
        },
    }

    # Save
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blind_path = output_dir / "pairability_v2_2_1_blind_packet.json"
    with open(blind_path, 'w') as f:
        json.dump({
            "packet_type": "BLIND_PAIRABILITY_ADJUDICATION_V2_2_1",
            "universe_manifest_hash": manifest_hash,
            "pair_count": len(blind_packets),
            "adjudication_questions": report["adjudication_questions"],
            "task_type_rules": report["task_type_rules"],
            "rules": [
                "Custodian must NOT see heuristic scores, strata, or dispositions before adjudicating.",
                "Answer A-I for every pair.",
                "I=YES is REQUIRED for benchmark candidacy.",
                "D1=NO alone does NOT establish S-TASK.",
                "If abstract status is not ABSTRACT_PRESENT, note in rationale.",
                "If <100 qualify, report NEGATIVE_RESULT.",
            ],
            "pairs": blind_packets,
        }, f, indent=2)

    full_path = output_dir / "pairability_v2_2_1_full_records.json"
    with open(full_path, 'w') as f:
        json.dump({
            "universe_manifest_hash": manifest_hash,
            "pair_count": len(full_records),
            "records": full_records,
        }, f, indent=2)

    report_path = output_dir / "pairability_v2_2_1_aggregate_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFiles saved:")
    print(f"  Blind packet: {blind_path}")
    print(f"  Full records: {full_path}")
    print(f"  Aggregate report: {report_path}")

    return report
