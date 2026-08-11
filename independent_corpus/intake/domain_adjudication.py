"""
independent_corpus.intake.domain_adjudication — Custodian domain adjudication.

Adjudicates the 100 METADATA_TOO_COARSE records against the EXISTING frozen taxonomy.
Does NOT modify the taxonomy. Does NOT construct source pairs. Does NOT let TEE see this.

Allowed classifications:
  - An existing frozen domain (e.g., "fluid_mechanics", "enzymology")
  - OUTSIDE_SCOPE (genuinely outside benchmark domain universe)
  - TAXONOMY_GAP (taxonomy genuinely lacks this discipline)
  - UNRESOLVED (cannot determine from available information)

Also: randomly samples 30-50 records for independent custodian adjudication,
then produces a confusion/disagreement report comparing automated vs custodian.
"""
import json
import random
import sys
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from custodian.src.domain_taxonomy import canonicalize_domain, is_known_domain, DOMAIN_TAXONOMY
from independent_corpus.intake.forensic_audit import (
    classify_forensic_reason,
    METADATA_TOO_COARSE,
    OUTSIDE_BENCHMARK_DOMAIN,
)

# Allowed adjudication outcomes
OUTSIDE_SCOPE = "OUTSIDE_SCOPE"
TAXONOMY_GAP = "TAXONOMY_GAP"
UNRESOLVED = "UNRESOLVED"


@dataclass
class AdjudicationRecord:
    """Custodian adjudication for a single record."""
    source_id: str
    openalex_domain: str  # Original OpenAlex domain
    automated_canonical_domain: str  # What the automated system produced
    automated_intake_status: str  # ELIGIBLE, FLAGGED, REJECTED
    forensic_reason_code: str  # From forensic audit
    # Bibliographic info for custodian review (NO full content)
    title: str  # Title is needed for domain classification
    doi: str
    publisher: str
    publication_date: str
    # Custodian adjudication
    custodian_classification: str = ""  # Frozen domain, OUTSIDE_SCOPE, TAXONOMY_GAP, UNRESOLVED
    custodian_rationale: str = ""
    adjudication_timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "openalex_domain": self.openalex_domain,
            "automated_canonical_domain": self.automated_canonical_domain,
            "automated_intake_status": self.automated_intake_status,
            "forensic_reason_code": self.forensic_reason_code,
            "title": self.title,
            "doi": self.doi,
            "publisher": self.publisher,
            "publication_date": self.publication_date,
            "custodian_classification": self.custodian_classification,
            "custodian_rationale": self.custodian_rationale,
            "adjudication_timestamp": self.adjudication_timestamp,
        }


def prepare_adjudication(
    custodian_manifest_path: Path,
    forensic_audit_path: Path,
    sample_size: int = 50,
    random_seed: int = 42,
) -> dict:
    """Prepare adjudication records for the custodian.

    Steps:
    1. Load custodian manifest (200 records)
    2. Load forensic audit (200 dispositions)
    3. Select the 100 METADATA_TOO_COARSE records
    4. Randomly sample 30-50 from ALL 200 for cross-validation
    5. Prepare bibliographic info (title, DOI, publisher — NO full text)
    6. Output: adjudication tasks for custodian

    Args:
        custodian_manifest_path: Path to custodian_intake_manifest.json
        forensic_audit_path: Path to forensic_audit_detailed.json
        sample_size: Number of records to sample for cross-validation (default 50)
        random_seed: Random seed for sampling (deterministic)

    Returns:
        Dict with adjudication tasks
    """
    # Load manifests
    with open(custodian_manifest_path) as f:
        intake_manifest = json.load(f)
    with open(forensic_audit_path) as f:
        forensic_audit = json.load(f)

    # Build forensic lookup
    forensic_lookup = {}
    for d in forensic_audit.get("dispositions", []):
        forensic_lookup[d["source_id"]] = d

    # Build intake lookup with bibliographic info
    intake_lookup = {}
    for r in intake_manifest.get("records", []):
        provenance = r.get("provenance", {})
        intake_lookup[r["source_id"]] = {
            "source_id": r["source_id"],
            "openalex_domain": r["domain"],
            "automated_canonical_domain": r["canonical_domain"],
            "automated_intake_status": r["intake_status"],
            "title": r.get("title", ""),
            "doi": provenance.get("doi", ""),
            "publisher": provenance.get("publisher", ""),
            "publication_date": provenance.get("publication_date", ""),
        }

    # Separate records by forensic reason
    metadata_coarse_records = []
    all_records = []

    for source_id, info in intake_lookup.items():
        forensic = forensic_lookup.get(source_id, {})
        reason_code = forensic.get("forensic_reason_code", "UNKNOWN")

        adj_record = AdjudicationRecord(
            source_id=source_id,
            openalex_domain=info["openalex_domain"],
            automated_canonical_domain=info["automated_canonical_domain"],
            automated_intake_status=info["automated_intake_status"],
            forensic_reason_code=reason_code,
            title=info["title"],
            doi=info["doi"],
            publisher=info["publisher"],
            publication_date=info["publication_date"],
        )

        all_records.append(adj_record)

        if reason_code == METADATA_TOO_COARSE:
            metadata_coarse_records.append(adj_record)

    # Randomly sample from ALL 200 for cross-validation
    random.seed(random_seed)
    sample_size = min(sample_size, len(all_records))
    cross_validation_sample = random.sample(all_records, sample_size)

    # Build output
    return {
        "adjudication_type": "CUSTODIAN_DOMAIN_ADJUDICATION_V1",
        "adjudication_version": "1.0.0",
        "frozen_taxonomy_domains": sorted(set(DOMAIN_TAXONOMY.values())),
        "allowed_classifications": [
            "Any existing frozen domain (e.g., fluid_mechanics, enzymology, optics, ...)",
            OUTSIDE_SCOPE,
            TAXONOMY_GAP,
            UNRESOLVED,
        ],
        "rules": [
            "Do NOT modify the frozen taxonomy during adjudication.",
            "Do NOT create new domain categories.",
            "Do NOT map 'close enough' — only exact scientific discipline match.",
            "If the paper genuinely belongs to a frozen domain, classify it.",
            "If it is genuinely outside the taxonomy, use OUTSIDE_SCOPE.",
            "If the taxonomy genuinely lacks a necessary discipline, use TAXONOMY_GAP.",
            "If you cannot determine from available info, use UNRESOLVED.",
            "Record a rationale for every classification.",
            "Never overwrite the automated classification.",
        ],
        "metadata_coarse_records": [r.to_dict() for r in metadata_coarse_records],
        "cross_validation_sample": [r.to_dict() for r in cross_validation_sample],
        "statistics": {
            "total_records": len(all_records),
            "metadata_coarse_count": len(metadata_coarse_records),
            "cross_validation_sample_size": len(cross_validation_sample),
            "random_seed": random_seed,
        },
    }


def compute_confusion_matrix(
    automated: List[str],
    custodian: List[str],
) -> dict:
    """Compute confusion matrix comparing automated vs custodian classification.

    Both lists must be the same length, aligned by index.

    "Eligible" = classified as a known frozen domain (not OUTSIDE_SCOPE/TAXONOMY_GAP/UNRESOLVED)
    """
    n = len(automated)
    tp = fp = fn = tn = 0  # "positive" = eligible

    for a, c in zip(automated, custodian):
        a_eligible = a not in (OUTSIDE_SCOPE, TAXONOMY_GAP, UNRESOLVED, "unknown", "")
        c_eligible = c not in (OUTSIDE_SCOPE, TAXONOMY_GAP, UNRESOLVED, "")

        if a_eligible and c_eligible:
            tp += 1
        elif a_eligible and not c_eligible:
            fp += 1  # Automated said eligible, custodian said no
        elif not a_eligible and c_eligible:
            fn += 1  # Automated said no, custodian said eligible
        else:
            tn += 1  # Both said no

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    accuracy = (tp + tn) / n if n > 0 else 0.0

    # Taxonomy gap rate
    taxonomy_gaps = sum(1 for c in custodian if c == TAXONOMY_GAP)

    return {
        "n": n,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "accuracy": round(accuracy, 4),
        "taxonomy_gap_rate": round(taxonomy_gaps / n, 4) if n > 0 else 0.0,
        "taxonomy_gap_count": taxonomy_gaps,
    }


def run_adjudication(
    custodian_manifest_path: Path,
    forensic_audit_path: Path,
    output_dir: Path,
    sample_size: int = 50,
    random_seed: int = 42,
) -> dict:
    """Run the full adjudication preparation.

    Produces:
    1. Adjudication tasks (for custodian to fill in)
    2. (Later) Confusion matrix when custodian returns adjudications
    """
    result = prepare_adjudication(
        custodian_manifest_path=custodian_manifest_path,
        forensic_audit_path=forensic_audit_path,
        sample_size=sample_size,
        random_seed=random_seed,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save adjudication tasks (custodian-only)
    tasks_path = output_dir / "domain_adjudication_tasks.json"
    with open(tasks_path, 'w') as f:
        json.dump(result, f, indent=2)

    # Print summary
    stats = result["statistics"]
    print("=== CUSTODIAN DOMAIN ADJUDICATION V1 ===")
    print()
    print(f"Total records: {stats['total_records']}")
    print(f"METADATA_TOO_COARSE records to adjudicate: {stats['metadata_coarse_count']}")
    print(f"Cross-validation sample size: {stats['cross_validation_sample_size']}")
    print(f"Random seed: {stats['random_seed']}")
    print()
    print("Allowed classifications:")
    for c in result["allowed_classifications"]:
        print(f"  - {c}")
    print()
    print("Rules:")
    for r in result["rules"]:
        print(f"  - {r}")
    print()
    print(f"Adjudication tasks saved: {tasks_path}")
    print()
    print("NEXT STEP: Custodian fills in custodian_classification + custodian_rationale")
    print("for each record, then runs the confusion matrix analysis.")
    print()

    # Also produce an automated pre-classification using simple heuristics
    # (the custodian reviews these, doesn't accept them automatically)
    automated_adjudications = _automated_pre_classification(result)
    auto_path = output_dir / "domain_adjudication_automated_preclassification.json"
    with open(auto_path, 'w') as f:
        json.dump(automated_adjudications, f, indent=2)
    print(f"Automated pre-classification saved: {auto_path}")
    print("(Custodian must review — do NOT accept automatically)")

    return result


def _automated_pre_classification(adjudication_data: dict) -> dict:
    """Generate automated pre-classification suggestions for the custodian.

    These are SUGGESTIONS, not decisions. The custodian must review each one.
    Uses simple keyword matching from the OpenAlex domain to frozen taxonomy.
    """
    suggestions = []

    # Mapping from OpenAlex domain keywords to frozen taxonomy domains
    keyword_mappings = {
        "engineering": ["mechanical_engineering", "chemical_engineering", "electrical_engineering"],
        "biochemistry": ["biochemistry", "molecular_biology", "enzymology"],
        "genetics": ["molecular_biology", "biochemistry"],
        "molecular_biology": ["molecular_biology", "biochemistry"],
        "computer_science": ["computer_science"],
        "physics": ["optics", "electromagnetics", "thermodynamics"],
        "astronomy": [OUTSIDE_SCOPE],
        "agricultural": [OUTSIDE_SCOPE],
        "biological": ["biology"],
        "energy": ["thermodynamics"],
        "immunology": [OUTSIDE_SCOPE],
        "microbiology": [OUTSIDE_SCOPE],
        "chemical_engineering": ["chemical_engineering"],
        "materials": ["materials_science"],
    }

    all_records = (
        adjudication_data.get("metadata_coarse_records", []) +
        adjudication_data.get("cross_validation_sample", [])
    )
    seen_ids = set()

    for record in all_records:
        if record["source_id"] in seen_ids:
            continue
        seen_ids.add(record["source_id"])

        openalex_domain = record["openalex_domain"].lower()
        suggested = UNRESOLVED
        rationale = "No keyword match found"

        for keyword, domains in keyword_mappings.items():
            if keyword in openalex_domain:
                if len(domains) == 1:
                    suggested = domains[0]
                    rationale = f"Keyword '{keyword}' in OpenAlex domain maps to '{suggested}'"
                else:
                    suggested = UNRESOLVED
                    rationale = f"Keyword '{keyword}' maps to multiple domains: {domains}. Requires custodian review."
                break

        suggestions.append({
            "source_id": record["source_id"],
            "openalex_domain": record["openalex_domain"],
            "suggested_classification": suggested,
            "rationale": rationale,
            "note": "SUGGESTION ONLY — custodian must review and confirm or override.",
        })

    return {
        "pre_classification_type": "AUTOMATED_SUGGESTION",
        "pre_classification_version": "1.0.0",
        "note": "These are automated suggestions for the custodian. They are NOT decisions. "
                "The custodian must review each one and record their own classification.",
        "suggestions": suggestions,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--output", default=".")
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_adjudication(
        custodian_manifest_path=Path(args.manifest),
        forensic_audit_path=Path(args.audit),
        output_dir=Path(args.output),
        sample_size=args.sample_size,
        random_seed=args.seed,
    )
