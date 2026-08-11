"""
independent_corpus.intake.forensic_audit — Custodian-only intake forensic audit.

Audits all 200 acquired records with reason-coded disposition.
Does NOT modify the frozen taxonomy, eligibility rules, or corpus.
Does NOT construct source pairs, run TEE, or generate hypotheses.

For each record, classifies the flag reason into:
1. OUTSIDE_BENCHMARK_DOMAIN — genuinely outside our domain universe
2. METADATA_TOO_COARSE — valid source but OpenAlex metadata doesn't map
3. DOMAIN_FROM_CONTENT — valid source, domain determinable from content
4. DUPLICATE_NEAR_DUPLICATE — duplicate or near-duplicate
5. INSUFFICIENT_PROVENANCE — provenance incomplete
6. INSUFFICIENT_FULL_TEXT — no full text available
7. OTHER — other reason

Also computes: estimated true-eligibility rate with Wilson confidence interval.
"""
import json
import sys
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from custodian.src.domain_taxonomy import canonicalize_domain, is_known_domain, DOMAIN_TAXONOMY


# Reason codes
OUTSIDE_BENCHMARK_DOMAIN = "OUTSIDE_BENCHMARK_DOMAIN"
METADATA_TOO_COARSE = "METADATA_TOO_COARSE"
DOMAIN_FROM_CONTENT = "DOMAIN_FROM_CONTENT"
DUPLICATE_NEAR_DUPLICATE = "DUPLICATE_NEAR_DUPLICATE"
INSUFFICIENT_PROVENANCE = "INSUFFICIENT_PROVENANCE"
INSUFFICIENT_FULL_TEXT = "INSUFFICIENT_FULL_TEXT"
OTHER = "OTHER"

REASON_CODES = [
    OUTSIDE_BENCHMARK_DOMAIN,
    METADATA_TOO_COARSE,
    DOMAIN_FROM_CONTENT,
    DUPLICATE_NEAR_DUPLICATE,
    INSUFFICIENT_PROVENANCE,
    INSUFFICIENT_FULL_TEXT,
    OTHER,
]


@dataclass
class RecordDisposition:
    """Forensic disposition for a single record."""
    source_id: str
    intake_status: str  # ELIGIBLE, FLAGGED, REJECTED
    domain_raw: str
    domain_canonical: str
    is_known_domain: bool
    has_full_text: bool
    exposure_status: str
    contamination_level: str
    flag_reasons: List[str]
    forensic_reason_code: str  # One of REASON_CODES
    forensic_notes: str
    custodian_adjudication: str = "PENDING"  # PENDING, PROMOTE, KEEP_FLAG, REJECT

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "intake_status": self.intake_status,
            "domain_raw": self.domain_raw,
            "domain_canonical": self.domain_canonical,
            "is_known_domain": self.is_known_domain,
            "has_full_text": self.has_full_text,
            "exposure_status": self.exposure_status,
            "contamination_level": self.contamination_level,
            "flag_reasons": self.flag_reasons,
            "forensic_reason_code": self.forensic_reason_code,
            "forensic_notes": self.forensic_notes,
            "custodian_adjudication": self.custodian_adjudication,
        }


def wilson_ci(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score confidence interval for a proportion.

    Args:
        p: observed proportion
        n: sample size
        z: z-score (1.96 for 95% CI)

    Returns:
        (lower, upper) bounds
    """
    if n == 0:
        return (0.0, 1.0)
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0, center - spread), min(1, center + spread))


def classify_forensic_reason(record: dict) -> Tuple[str, str]:
    """Classify the forensic reason for a flagged record.

    Returns (reason_code, notes).
    """
    domain_raw = record.get("domain", "unknown")
    domain_canonical = record.get("canonical_domain", "unknown")
    flags = record.get("flags", [])
    exposure = record.get("exposure", {}).get("status", "UNSEEN")
    contamination = record.get("contamination", {}).get("level", "CLEAN")
    has_full_text = bool(record.get("provenance", {}).get("full_text_uri"))

    # Check if domain is known
    is_known = is_known_domain(domain_raw)

    # Check flag reasons — use precise matching to avoid false positives
    domain_flag = any("not in frozen taxonomy" in f for f in flags)
    near_dup_flag = any("NEAR_DUPLICATE" in f for f in flags)
    exposure_flag = any("POSSIBLY_SEEN" in f or "KNOWN_SEEN" in f for f in flags)
    contamination_flag = any("CONTAMINATED" in f or "HYPOTHESIS_LANGUAGE" in f or "RELATIONSHIP_REVEAL" in f or "EXPLICIT_BRIDGE" in f for f in flags)

    # Classify
    if near_dup_flag:
        return (DUPLICATE_NEAR_DUPLICATE, "Near-duplicate detected during intake")

    if exposure_flag:
        return (OTHER, f"Exposure flag: {exposure}")

    if contamination_flag:
        return (OTHER, f"Contamination flag: {contamination}")

    if domain_flag and not is_known:
        # Domain is not in the frozen taxonomy
        # Normalize for comparison
        domain_norm = domain_raw.lower().replace(" ", "_").replace(",", "")

        # OpenAlex field-level categories and their forensic classification
        openalex_domain_mappings = {
            "engineering": (METADATA_TOO_COARSE, "Could map to mechanical_engineering or chemical_engineering"),
            "medicine": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope (medical science)"),
            "biochemistry_genetics_and_molecular_biology": (METADATA_TOO_COARSE, "Could partially map to biochemistry or molecular_biology"),
            "computer_science": (METADATA_TOO_COARSE, "Known domain — OpenAlex naming differs from frozen taxonomy"),
            "social_sciences": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "environmental_science": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "agricultural_and_biological_sciences": (METADATA_TOO_COARSE, "Could partially map to biology"),
            "physics_and_astronomy": (METADATA_TOO_COARSE, "Could partially map to optics or electromagnetics"),
            "economics_econometrics_and_finance": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "neuroscience": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "business_management_and_accounting": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "decision_sciences": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "health_professions": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "earth_and_planetary_sciences": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "arts_and_humanities": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "pharmacology_toxicology_and_pharmaceutics": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "mathematics": (OUTSIDE_BENCHMARK_DOMAIN, "Genuinely outside current benchmark scope"),
            "energy": (METADATA_TOO_COARSE, "Could partially map to thermodynamics"),
            "immunology_and_microbiology": (METADATA_TOO_COARSE, "Could partially map to biology"),
            "chemical_engineering": (METADATA_TOO_COARSE, "Known domain — OpenAlex uses same name as frozen taxonomy"),
        }

        if domain_norm in openalex_domain_mappings:
            reason, notes = openalex_domain_mappings[domain_norm]
            return (reason, f"OpenAlex domain '{domain_raw}' — {notes}")
        else:
            return (OUTSIDE_BENCHMARK_DOMAIN, f"Domain '{domain_raw}' (normalized: '{domain_norm}') not recognized in any mapping")

    if not has_full_text:
        return (INSUFFICIENT_FULL_TEXT, "No open-access full text available")

    # If we get here, check provenance
    provenance = record.get("provenance", {})
    if not provenance.get("doi"):
        return (INSUFFICIENT_PROVENANCE, "Missing DOI")

    return (OTHER, "Unclassified flag")


def run_forensic_audit(custodian_manifest_path: Path) -> dict:
    """Run forensic audit on the custodian intake manifest.

    Args:
        custodian_manifest_path: Path to custodian_intake_manifest.json

    Returns:
        Audit report dict (custodian-only, contains source_ids but NO content)
    """
    with open(custodian_manifest_path) as f:
        manifest = json.load(f)

    records = manifest.get("records", [])
    dispositions = []

    for record in records:
        reason_code, notes = classify_forensic_reason(record)
        disposition = RecordDisposition(
            source_id=record["source_id"],
            intake_status=record["intake_status"],
            domain_raw=record["domain"],
            domain_canonical=record["canonical_domain"],
            is_known_domain=is_known_domain(record["domain"]),
            has_full_text=bool(record.get("provenance", {}).get("full_text_uri")),
            exposure_status=record.get("exposure", {}).get("status", "UNSEEN"),
            contamination_level=record.get("contamination", {}).get("level", "CLEAN"),
            flag_reasons=record.get("flags", []),
            forensic_reason_code=reason_code,
            forensic_notes=notes,
        )
        dispositions.append(disposition)

    # Compute statistics
    n_total = len(dispositions)
    n_eligible = sum(1 for d in dispositions if d.intake_status == "ELIGIBLE")
    n_flagged = sum(1 for d in dispositions if d.intake_status == "FLAGGED")
    n_rejected = sum(1 for d in dispositions if d.intake_status == "REJECTED")

    # Reason code distribution (for flagged records)
    reason_counts = Counter()
    for d in dispositions:
        if d.intake_status == "FLAGGED":
            reason_counts[d.forensic_reason_code] += 1

    # Estimated true-eligibility rate
    # "True eligible" = currently eligible + flagged records that COULD be promoted
    # (METADATA_TOO_COARSE, DOMAIN_FROM_CONTENT) — these are valid papers with
    # metadata/domain issues that the custodian might resolve
    potentially_promotable = sum(
        1 for d in dispositions
        if d.intake_status == "FLAGGED"
        and d.forensic_reason_code in (METADATA_TOO_COARSE, DOMAIN_FROM_CONTENT)
    )
    truly_outside = sum(
        1 for d in dispositions
        if d.forensic_reason_code == OUTSIDE_BENCHMARK_DOMAIN
    )

    # Conservative estimate: only currently eligible are true eligible
    # Optimistic estimate: eligible + promotable
    conservative_rate = n_eligible / n_total if n_total > 0 else 0
    optimistic_rate = (n_eligible + potentially_promotable) / n_total if n_total > 0 else 0

    # Wilson CI for conservative rate
    ci_lower, ci_upper = wilson_ci(conservative_rate, n_total)

    # Calculate required acquisition size for N>=100 eligible
    # Using conservative rate
    if conservative_rate > 0:
        required_for_100_conservative = int(math.ceil(100 / conservative_rate))
    else:
        required_for_100_conservative = float('inf')

    if optimistic_rate > 0:
        required_for_100_optimistic = int(math.ceil(100 / optimistic_rate))
    else:
        required_for_100_optimistic = float('inf')

    # Build aggregate report (TEE-safe: no titles, no content)
    aggregate_report = {
        "report_type": "INTAKE_FORENSIC_AUDIT_AGGREGATE",
        "report_version": "1.0.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "source_manifest_hash": manifest.get("source_registry_hash", "unknown"),
        "total_records": n_total,
        "eligible": n_eligible,
        "flagged": n_flagged,
        "rejected": n_rejected,
        "flagged_reason_distribution": dict(reason_counts.most_common()),
        "potentially_promotable": potentially_promotable,
        "truly_outside_domain": truly_outside,
        "estimated_true_eligibility": {
            "conservative_rate": round(conservative_rate, 4),
            "optimistic_rate": round(optimistic_rate, 4),
            "wilson_95ci_lower": round(ci_lower, 4),
            "wilson_95ci_upper": round(ci_upper, 4),
            "n_sample": n_total,
        },
        "required_acquisition_for_n100": {
            "conservative": required_for_100_conservative,
            "optimistic": required_for_100_optimistic,
            "note": "If conservative rate holds, acquire this many papers to get ~100 eligible.",
        },
        "note": "This report contains NO paper titles, NO content. Only aggregate statistics. "
                "39 passed automated eligibility; 161 require review. "
                "This is NOT '39 good papers and 161 bad papers.'",
    }

    # Build detailed custodian-only manifest
    detailed_manifest = {
        "manifest_type": "INTAKE_FORENSIC_AUDIT_DETAILED",
        "manifest_version": "1.0.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "source_manifest_hash": manifest.get("source_registry_hash", "unknown"),
        "total_records": n_total,
        "dispositions": [d.to_dict() for d in dispositions],
        "reason_code_definitions": {
            OUTSIDE_BENCHMARK_DOMAIN: "Genuinely outside our benchmark domain universe",
            METADATA_TOO_COARSE: "Valid source but OpenAlex metadata doesn't map to frozen taxonomy",
            DOMAIN_FROM_CONTENT: "Valid source, domain determinable from content (not metadata)",
            DUPLICATE_NEAR_DUPLICATE: "Duplicate or near-duplicate detected",
            INSUFFICIENT_PROVENANCE: "Provenance incomplete (e.g., missing DOI)",
            INSUFFICIENT_FULL_TEXT: "No open-access full text available",
            OTHER: "Other reason (exposure, contamination, unclassified)",
        },
        "custodian_adjudication_status": "PENDING — custodian must review each disposition",
        "note": "CUSTODIAN-ONLY. Contains source_ids but NO content. "
                "No TEE access. No benchmark construction.",
    }

    return {
        "aggregate_report": aggregate_report,
        "detailed_manifest": detailed_manifest,
        "dispositions": dispositions,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="Path to custodian_intake_manifest.json")
    parser.add_argument("--output", default=".", help="Output directory")
    args = parser.parse_args()

    result = run_forensic_audit(Path(args.manifest))

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save aggregate report (TEE-safe)
    with open(output_dir / "forensic_audit_aggregate.json", 'w') as f:
        json.dump(result["aggregate_report"], f, indent=2)

    # Save detailed manifest (custodian-only)
    with open(output_dir / "forensic_audit_detailed.json", 'w') as f:
        json.dump(result["detailed_manifest"], f, indent=2)

    # Print summary
    ar = result["aggregate_report"]
    print("=== INTAKE FORENSIC AUDIT ===")
    print()
    print(f"Total records: {ar['total_records']}")
    print(f"Eligible: {ar['eligible']}")
    print(f"Flagged: {ar['flagged']}")
    print(f"Rejected: {ar['rejected']}")
    print()
    print("Flagged reason distribution:")
    for reason, count in ar["flagged_reason_distribution"].items():
        print(f"  {reason}: {count}")
    print()
    print(f"Potentially promotable: {ar['potentially_promotable']}")
    print(f"Truly outside domain: {ar['truly_outside_domain']}")
    print()
    est = ar["estimated_true_eligibility"]
    print(f"Estimated true-eligibility rate:")
    print(f"  Conservative: {est['conservative_rate']:.1%} (95% CI: {est['wilson_95ci_lower']:.1%} - {est['wilson_95ci_upper']:.1%})")
    print(f"  Optimistic: {est['optimistic_rate']:.1%}")
    print()
    req = ar["required_acquisition_for_n100"]
    print(f"Required acquisition for N>=100 eligible:")
    print(f"  Conservative: {req['conservative']:,} papers")
    print(f"  Optimistic: {req['optimistic']:,} papers")
    print()
    print("NOTE: 39 passed automated eligibility; 161 require review.")
    print("This is NOT '39 good papers and 161 bad papers.'")
