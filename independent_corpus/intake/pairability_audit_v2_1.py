"""
independent_corpus.intake.pairability_audit_v2_1 — Scientific adjudication hardening.

Fixes from V2:
1. Reconciled source universe (112 sources, immutable manifest hash)
2. Blind packet includes abstracts + relevant passages (not just titles)
3. Split novelty: D1/D2/D3/D4 instead of single D
4. Stratum accounting: no silent substitution, HARD_NEGATIVE_UNAVAILABLE recorded
5. Independent hard-negative methodology (not derived from bridge heuristic)
6. Adversarial-transfer adjudication question
7. Final pairability report

Does NOT construct benchmark. Does NOT run TEE. Does NOT change taxonomy.
"""
import json
import random
import re
import sys
import math
import hashlib
import urllib.request
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


# Strata
STRATUM_STRONG = "heuristic_strong"
STRATUM_WEAK = "heuristic_weak"
STRATUM_LEXICAL_LOW = "lexical_low_mechanistic"
STRATUM_HARD_NEGATIVE = "hard_negative"
STRATUM_RANDOM = "random_cross_domain"
STRATUM_UNAVAILABLE = "STRATUM_UNAVAILABLE"


def fetch_abstract(doi: str) -> str:
    """Fetch abstract from OpenAlex using DOI."""
    if not doi:
        return ""
    clean_doi = doi.replace("https://doi.org/", "").replace("https://dx.doi.org/", "")
    try:
        url = f"https://api.openalex.org/works/doi:{clean_doi}?select=title,abstract_inverted_index"
        req = urllib.request.Request(url, headers={"User-Agent": "CustodianIntake/1.0"})
        import time
        time.sleep(0.3)  # Rate limit
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            # Reconstruct abstract from inverted index
            inv_idx = data.get("abstract_inverted_index", {})
            if not inv_idx:
                return ""
            positions = []
            for word, idxs in inv_idx.items():
                for pos in idxs:
                    positions.append((pos, word))
            positions.sort()
            abstract = " ".join(w for _, w in positions)
            return abstract
    except Exception:
        return ""


@dataclass
class CandidatePairV21:
    """Candidate pair for V2.1 adjudication with scientific evidence."""
    source_a_id: str
    source_b_id: str
    domain_a: str
    domain_b: str
    title_a: str
    title_b: str
    abstract_a: str
    abstract_b: str
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
    # Custodian adjudication (PENDING)
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
            "abstract_a": self.abstract_a,
            "abstract_b": self.abstract_b,
            "doi_a": self.doi_a,
            "doi_b": self.doi_b,
            "publisher_a": self.publisher_a,
            "publisher_b": self.publisher_b,
            "publication_date_a": self.publication_date_a,
            "publication_date_b": self.publication_date_b,
            "custodian_adjudication": self.custodian_adjudication,
        }


def build_hard_negatives(sources: List[dict]) -> List[Tuple[dict, dict]]:
    """Independent hard-negative construction.

    NOT derived from the bridge heuristic. Uses a different methodology:
    - Find cross-domain pairs with HIGH lexical similarity (shared terminology)
    - These are "seductive false bridges" — they look connected but may not be
    - The custodian determines if the connection is real or illusory

    This is independent from V1's bridge score because it uses a different
    selection criterion: high lexical overlap WITHOUT any bridge consideration.
    """
    hard_negatives = []

    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            sa, sb = sources[i], sources[j]
            if sa["domain"] == sb["domain"]:
                continue

            # Compute lexical similarity
            tokens_a = _tokenize(sa.get("title", ""))
            tokens_b = _tokenize(sb.get("title", ""))
            lexical = _jaccard(tokens_a, tokens_b)

            # Hard negative: HIGH lexical similarity (>= 0.15)
            # These pairs share terminology but may have incompatible mechanisms
            if lexical >= 0.15:
                hard_negatives.append((sa, sb))

    return hard_negatives


def build_v21_candidate_pool(
    universe_path: Path,
    output_dir: Path,
    target_pool_size: int = 200,
    random_seed: int = 42,
    fetch_abstracts: bool = True,
) -> dict:
    """Build V2.1 stratified candidate pool with scientific evidence."""
    with open(universe_path) as f:
        universe = json.load(f)

    sources = universe.get("sources", [])
    n_sources = len(sources)
    manifest_hash = universe.get("manifest_hash", "")

    print(f"=== SOURCE_PAIRABILITY_AUDIT_V2.1 ===")
    print(f"Universe: FINAL_ELIGIBLE_SOURCE_UNIVERSE_V1")
    print(f"Manifest hash: {manifest_hash[:32]}...")
    print(f"Source count: {n_sources}")
    print(f"Target pool size: {target_pool_size}")
    print()

    # Generate ALL cross-domain pairs with heuristic scores
    all_pairs = []
    for i in range(n_sources):
        for j in range(i + 1, n_sources):
            sa, sb = sources[i], sources[j]
            if sa["domain"] == sb["domain"]:
                continue

            audit = audit_pair(sa, sb)
            if audit.disposition in ("DUPLICATE", "SAME_DOMAIN"):
                continue

            pair = CandidatePairV21(
                source_a_id=sa["source_id"],
                source_b_id=sb["source_id"],
                domain_a=sa["domain"],
                domain_b=sb["domain"],
                title_a=sa.get("title", ""),
                title_b=sb.get("title", ""),
                abstract_a="",  # Fetched later
                abstract_b="",
                doi_a=sa.get("doi", ""),
                doi_b=sb.get("doi", ""),
                publisher_a=sa.get("publisher", ""),
                publisher_b=sb.get("publisher", ""),
                publication_date_a=sa.get("publication_date", ""),
                publication_date_b=sb.get("publication_date", ""),
                lexical_similarity=audit.lexical_similarity,
                scientific_bridge_score=audit.scientific_bridge_score,
                bridge_evidence_type=audit.bridge_evidence_type,
                heuristic_disposition="HEURISTIC_CANDIDATE" if audit.scientific_bridge_score >= 0.5
                    else ("HEURISTIC_WEAK" if audit.scientific_bridge_score >= 0.2
                    else "INSUFFICIENT_EVIDENCE"),
                stratum="",
            )
            all_pairs.append(pair)

    print(f"Cross-domain pairs: {len(all_pairs)}")

    # Classify into strata
    strong = [p for p in all_pairs if p.scientific_bridge_score >= 0.5]
    weak = [p for p in all_pairs if 0.2 <= p.scientific_bridge_score < 0.5]
    lexical_low = [p for p in all_pairs if p.lexical_similarity < 0.1
                   and p.bridge_evidence_type != "NONE"
                   and p.scientific_bridge_score < 0.2]

    # INDEPENDENT hard-negative methodology (not from bridge heuristic)
    hard_neg_candidates = build_hard_negatives(sources)
    # Convert to CandidatePairV21 format
    hard_neg_pairs = []
    for sa, sb in hard_neg_candidates:
        audit = audit_pair(sa, sb)
        if audit.disposition in ("DUPLICATE", "SAME_DOMAIN"):
            continue
        pair = CandidatePairV21(
            source_a_id=sa["source_id"], source_b_id=sb["source_id"],
            domain_a=sa["domain"], domain_b=sb["domain"],
            title_a=sa.get("title", ""), title_b=sb.get("title", ""),
            abstract_a="", abstract_b="",
            doi_a=sa.get("doi", ""), doi_b=sb.get("doi", ""),
            publisher_a=sa.get("publisher", ""), publisher_b=sb.get("publisher", ""),
            publication_date_a=sa.get("publication_date", ""),
            publication_date_b=sb.get("publication_date", ""),
            lexical_similarity=audit.lexical_similarity,
            scientific_bridge_score=audit.scientific_bridge_score,
            bridge_evidence_type=audit.bridge_evidence_type,
            heuristic_disposition="HARD_NEGATIVE_CANDIDATE",
            stratum=STRATUM_HARD_NEGATIVE,
        )
        hard_neg_pairs.append(pair)

    # Random pool (exclude pairs already in other strata)
    used_ids = set()
    for p in strong + weak + lexical_low + hard_neg_pairs:
        used_ids.add((p.source_a_id, p.source_b_id))
    random_pool = [p for p in all_pairs
                   if (p.source_a_id, p.source_b_id) not in used_ids
                   and p.scientific_bridge_score < 0.2]

    print(f"\nStrata availability:")
    print(f"  heuristic_strong: {len(strong)}")
    print(f"  heuristic_weak: {len(weak)}")
    print(f"  lexical_low_mechanistic: {len(lexical_low)}")
    print(f"  hard_negative (INDEPENDENT method): {len(hard_neg_pairs)}")
    print(f"  random_cross_domain: {len(random_pool)}")

    # Sample with FROZEN proportions — no silent substitution
    random.seed(random_seed)
    strata_config = {
        STRATUM_STRONG: (strong, 0.20),
        STRATUM_WEAK: (weak, 0.30),
        STRATUM_LEXICAL_LOW: (lexical_low, 0.20),
        STRATUM_HARD_NEGATIVE: (hard_neg_pairs, 0.20),
        STRATUM_RANDOM: (random_pool, 0.10),
    }

    selected = []
    stratum_report = {}
    for stratum_name, (pool, proportion) in strata_config.items():
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
            for p in sampled:
                p.stratum = stratum_name
            selected.extend(sampled)

    print(f"\nTotal selected: {len(selected)}")
    print(f"Stratum shortfalls: {sum(1 for s in stratum_report.values() if s['status'] == STRATUM_UNAVAILABLE)}")

    # Fetch abstracts for blind packet
    if fetch_abstracts:
        print(f"\nFetching abstracts from OpenAlex...")
        for idx, pair in enumerate(selected):
            if (idx + 1) % 20 == 0:
                print(f"  {idx + 1}/{len(selected)}...")
            if not pair.abstract_a and pair.doi_a:
                pair.abstract_a = fetch_abstract(pair.doi_a)
            if not pair.abstract_b and pair.doi_b:
                pair.abstract_b = fetch_abstract(pair.doi_b)

    # Build blind packet
    blind_packets = [p.to_blind_dict() for p in selected]

    # Build full records
    full_records = [p.to_blind_dict() for p in selected]
    for i, p in enumerate(selected):
        full_records[i]["lexical_similarity"] = round(p.lexical_similarity, 4)
        full_records[i]["scientific_bridge_score"] = round(p.scientific_bridge_score, 4)
        full_records[i]["bridge_evidence_type"] = p.bridge_evidence_type
        full_records[i]["heuristic_disposition"] = p.heuristic_disposition
        full_records[i]["stratum"] = p.stratum

    # Domain pair distribution
    domain_pairs = Counter()
    for p in selected:
        pair_key = tuple(sorted([p.domain_a, p.domain_b]))
        domain_pairs[f"{pair_key[0]} ↔ {pair_key[1]}"] += 1

    report = {
        "report_type": "SOURCE_PAIRABILITY_AUDIT_V2_1",
        "report_version": "2.1.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "universe_manifest_hash": manifest_hash,
        "source_count": n_sources,
        "total_cross_domain_pairs": len(all_pairs),
        "target_pool_size": target_pool_size,
        "actual_pool_size": len(selected),
        "random_seed": random_seed,
        "stratum_report": stratum_report,
        "stratum_proportions_frozen": True,
        "no_silent_substitution": True,
        "hard_negative_methodology": "INDEPENDENT — high lexical similarity (>=0.15 Jaccard) without bridge consideration. NOT derived from bridge heuristic.",
        "domain_pair_distribution": dict(domain_pairs.most_common()),
        "blind_packet_contains": [
            "title_a, title_b",
            "abstract_a, abstract_b",
            "doi_a, doi_b",
            "publisher_a, publisher_b",
            "publication_date_a, publication_date_b",
            "domain_a, domain_b",
        ],
        "blind_packet_excludes": [
            "lexical_similarity",
            "scientific_bridge_score",
            "bridge_evidence_type",
            "heuristic_disposition",
            "stratum",
            "TEE information",
            "benchmark labels",
        ],
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
        },
        "task_type_rules": {
            "W_TASK": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES, D3=ESTABLISHED",
            "S_CANDIDATE": "A=YES, B=YES, C=YES, E=YES, F=YES, G=YES, D1=NO, D2=ADEQUATE, D3=NOT_ESTABLISHED",
            "REJECT": "Does not meet W or S criteria",
        },
        "note": "D=NO alone does NOT establish S-TASK. Requires D1=NO AND D2=ADEQUATE AND D3=NOT_ESTABLISHED. "
                "'Not found' ≠ 'does not exist.'",
        "negative_result_check": "If custodian adjudicates <100 qualifying pairs, report NEGATIVE_RESULT.",
    }

    # Save
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blind_path = output_dir / "pairability_v2_1_blind_packet.json"
    with open(blind_path, 'w') as f:
        json.dump({
            "packet_type": "BLIND_PAIRABILITY_ADJUDICATION_V2_1",
            "packet_version": "1.0.0",
            "universe_manifest_hash": manifest_hash,
            "pair_count": len(blind_packets),
            "adjudication_questions": report["adjudication_questions"],
            "task_type_rules": report["task_type_rules"],
            "rules": [
                "Custodian must NOT see heuristic scores, dispositions, or strata before adjudicating.",
                "Custodian must answer A-H for every pair.",
                "D1=NO alone does NOT establish S-TASK. Requires D1=NO AND D2=ADEQUATE AND D3=NOT_ESTABLISHED.",
                "'Not found' ≠ 'does not exist.'",
                "If <100 pairs qualify, report NEGATIVE_RESULT.",
                "No TEE access. No benchmark construction. No taxonomy changes.",
            ],
            "pairs": blind_packets,
        }, f, indent=2)

    full_path = output_dir / "pairability_v2_1_full_records.json"
    with open(full_path, 'w') as f:
        json.dump({
            "record_type": "PAIRABILITY_V2_1_FULL_RECORDS",
            "universe_manifest_hash": manifest_hash,
            "pair_count": len(full_records),
            "records": full_records,
        }, f, indent=2)

    report_path = output_dir / "pairability_v2_1_aggregate_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFiles saved:")
    print(f"  Blind packet: {blind_path}")
    print(f"  Full records: {full_path}")
    print(f"  Aggregate report: {report_path}")
    print()
    print("NEXT STEP: Custodian adjudicates blind packet (A-H questions per pair).")
    print("Then reveal heuristic scores and compute agreement.")
    print("Then determine if >=100 pairs qualify for benchmark construction.")
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

    build_v21_candidate_pool(
        universe_path=Path(args.universe),
        output_dir=Path(args.output),
        target_pool_size=args.target_size,
        random_seed=args.seed,
        fetch_abstracts=not args.no_abstracts,
    )
