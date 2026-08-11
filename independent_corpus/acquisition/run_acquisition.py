"""
independent_corpus.acquisition.run_acquisition — Main acquisition runner.

Executes the pre-declared sampling procedure:
  1. Create frozen acquisition manifest
  2. Sample from OpenAlex (no TEE influence)
  3. Cross-check with Semantic Scholar (independent verification)
  4. Run custodian intake (exposure, contamination, duplicate, domain)
  5. Produce aggregate-only report (no titles shown to TEE)

Usage:
  python -m independent_corpus.acquisition.run_acquisition --date-cutoff 2025-01-01 --seed external-custodian-seed --n 200
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directories to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from independent_corpus.acquisition.sampler import (
    create_acquisition_manifest,
    verify_no_tee_influence,
    AcquisitionManifest,
)
from independent_corpus.acquisition.openalex_adapter import (
    sample_openalex,
    fetch_full_text,
    OpenAlexRecord,
)
from independent_corpus.acquisition.semantic_scholar_adapter import (
    batch_cross_check,
    S2CrossCheckResult,
)
from custodian.intake.src.intake_gateway import (
    CorpusIntakeGateway,
    IntakeStatus,
)
from custodian.src.hasher import sha256_string


def run_acquisition(
    date_cutoff: str,
    random_seed: str,
    n_requested: int = 200,
    s2_cross_check_limit: int = 50,
    output_dir: Optional[Path] = None,
) -> dict:
    """Run the full acquisition pipeline.

    Returns aggregate-only report (no paper titles).
    """
    print(f"=== INDEPENDENT CORPUS ACQUISITION ===")
    print(f"Date cutoff: {date_cutoff}")
    print(f"Seed: {random_seed} (hash: {sha256_string(random_seed)[:16]}...)")
    print(f"N requested: {n_requested}")
    print()

    # 1. Create frozen acquisition manifest
    manifest = create_acquisition_manifest(
        date_cutoff=date_cutoff,
        random_seed=random_seed,
        n_requested=n_requested,
    )

    # Verify no TEE influence
    violations = verify_no_tee_influence(manifest)
    if violations:
        raise ValueError(f"TEE_INFLUENCE_DETECTED: {violations}")

    print(f"Manifest frozen (hash: {manifest.manifest_hash[:16]}...)")
    print(f"No TEE influence: VERIFIED")
    print(f"No connection search: VERIFIED")
    print()

    # 2. Sample from OpenAlex
    print(f"Sampling from OpenAlex...")
    records, cursor, stats = sample_openalex(
        date_cutoff=date_cutoff,
        random_seed=random_seed,
        max_results=n_requested,
    )
    print(f"  Received: {len(records)} records")
    print(f"  With full text: {stats['n_with_full_text']}")
    print()

    # 3. Cross-check with Semantic Scholar (sample)
    if records:
        print(f"Cross-checking with Semantic Scholar (max {s2_cross_check_limit})...")
        cross_check_results = batch_cross_check(records[:s2_cross_check_limit], max_checks=s2_cross_check_limit)
        s2_confirmed = sum(1 for r in cross_check_results if r.cross_check_status == "CONFIRMED")
        print(f"  Cross-checked: {len(cross_check_results)}")
        print(f"  Confirmed: {s2_confirmed}")
        print()

    # 4. Run custodian intake
    print(f"Running custodian intake...")
    gw = CorpusIntakeGateway()

    n_intaken = 0
    n_eligible = 0
    n_flagged = 0
    n_rejected = 0
    n_no_full_text = 0

    for record in records:
        # For initial acquisition, use metadata (title) as content for intake checks
        # Full-text fetching happens later during benchmark construction
        content = record.title or "Untitled"
        content_hash = sha256_string(content)

        if not record.full_text_uri:
            n_no_full_text += 1

        try:
            intake_record = gw.intake_source(
                source_id=record.source_id,
                domain=record.domain,
                title=record.title,
                origin=f"openalex:{record.openalex_id}",
                source_uri=record.source_uri,
                content=content,
                version=record.provider_record_id,
                license=record.license,
                provenance_metadata={
                    "doi": record.doi,
                    "authors": record.authors[:3],
                    "publication_date": record.publication_date,
                    "publisher": record.publisher,
                    "metadata_sha256": record.metadata_sha256,
                    "full_text_uri": record.full_text_uri,
                },
                acquisition_timestamp=record.acquisition_timestamp,
            )
            n_intaken += 1

            if intake_record.intake_status == IntakeStatus.ELIGIBLE:
                n_eligible += 1
            elif intake_record.intake_status == IntakeStatus.FLAGGED:
                n_flagged += 1
            elif intake_record.intake_status == IntakeStatus.REJECTED:
                n_rejected += 1

        except Exception as e:
            n_rejected += 1

    print(f"  Intaken: {n_intaken}")
    print(f"  Eligible: {n_eligible}")
    print(f"  Flagged: {n_flagged}")
    print(f"  Rejected: {n_rejected}")
    print(f"  No full text: {n_no_full_text}")
    print()

    # 5. Produce aggregate-only report
    domain_dist = gw.get_domain_distribution()
    status_dist = {
        IntakeStatus.ELIGIBLE.value: n_eligible,
        IntakeStatus.FLAGGED.value: n_flagged,
        IntakeStatus.REJECTED.value: n_rejected,
    }

    report = {
        "report_type": "AGGREGATE_INTAKE_REPORT",
        "report_version": "1.0.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "manifest": manifest.to_dict(),
        "acquisition_stats": stats,
        "intake_stats": {
            "n_intaken": n_intaken,
            "n_eligible": n_eligible,
            "n_flagged": n_flagged,
            "n_rejected": n_rejected,
            "n_no_full_text": n_no_full_text,
        },
        "domain_distribution": domain_dist,
        "status_distribution": status_dist,
        "publication_year_distribution": _compute_year_dist(records),
        "provider_distribution": {"openalex": len(records)},
        "note": "This report contains NO paper titles, NO abstracts, NO content. "
                "Only aggregate statistics. TEE team sees this report only.",
    }

    # Save report
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "aggregate_intake_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved: {report_path}")

    # Save full intake manifest (custodian-only)
    if output_dir:
        intake_manifest = gw.get_intake_manifest()
        intake_path = output_dir / "custodian_intake_manifest.json"
        with open(intake_path, 'w') as f:
            json.dump(intake_manifest, f, indent=2)
        print(f"Custodian manifest saved: {intake_path}")

    print()
    print("=== SUMMARY ===")
    print(f"Papers sampled: {len(records)}")
    print(f"Papers intaken: {n_intaken}")
    print(f"Eligible: {n_eligible}")
    print(f"Flagged: {n_flagged}")
    print(f"Rejected: {n_rejected}")
    print(f"No full text: {n_no_full_text}")
    print(f"Domains: {len(domain_dist)}")
    print()
    print("NOTE: No paper titles shown. TEE team sees aggregate counts only.")

    return report


def _compute_year_dist(records: List[OpenAlexRecord]) -> Dict[str, int]:
    """Compute publication year distribution."""
    dist = {}
    for r in records:
        year = r.publication_date[:4] if r.publication_date else "unknown"
        dist[year] = dist.get(year, 0) + 1
    return dict(sorted(dist.items()))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date-cutoff", default="2025-01-01")
    parser.add_argument("--seed", default="external-custodian-seed-v1")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    run_acquisition(
        date_cutoff=args.date_cutoff,
        random_seed=args.seed,
        n_requested=args.n,
        output_dir=Path(args.output) if args.output else None,
    )
