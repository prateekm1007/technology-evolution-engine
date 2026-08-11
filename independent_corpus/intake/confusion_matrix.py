"""
independent_corpus.intake.confusion_matrix — Compute confusion matrix for blinded cross-validation.

Reveals automated classifications for the same 50 source_ids that the custodian
independently adjudicated, then computes:
  - confusion matrix (TP/FP/FN/TN)
  - precision, recall, FPR, FNR
  - taxonomy-gap detection rate
  - per-domain errors
  - overall agreement
"""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))


def compute_cross_validation_analysis(
    custodian_result_path: Path,
    intake_manifest_path: Path,
    output_path: Path,
):
    """Compute confusion matrix and analysis.

    Args:
        custodian_result_path: Path to custodian_cross_validation_adjudication_v1.json
        intake_manifest_path: Path to custodian_intake_manifest.json
        output_path: Where to save the analysis
    """
    # Load custodian adjudication
    with open(custodian_result_path) as f:
        custodian_data = json.load(f)

    # Load intake manifest (for automated classifications)
    with open(intake_manifest_path) as f:
        manifest = json.load(f)

    # Build automated lookup
    automated_lookup = {}
    for r in manifest.get("records", []):
        sid = r["source_id"]
        automated_lookup[sid] = {
            "automated_intake_status": r["intake_status"],
            "automated_domain": r["domain"],
            "automated_canonical_domain": r["canonical_domain"],
            "flags": r.get("flags", []),
        }

    # Build custodian lookup
    custodian_lookup = {}
    for r in custodian_data.get("results", []):
        custodian_lookup[r["source_id"]] = {
            "custodian_classification": r["custodian_classification"],
            "custodian_rationale": r.get("custodian_rationale", ""),
        }

    # Match records
    matched = []
    for sid, auto in automated_lookup.items():
        if sid in custodian_lookup:
            cust = custodian_lookup[sid]
            matched.append({
                "source_id": sid,
                "automated_intake_status": auto["automated_intake_status"],
                "automated_domain": auto["automated_domain"],
                "automated_canonical_domain": auto["automated_canonical_domain"],
                "custodian_classification": cust["custodian_classification"],
                "custodian_rationale": cust["custodian_rationale"],
            })

    print(f"Matched records: {len(matched)} / 50")

    # Define "eligible" = classified as a known frozen domain
    # (not OUTSIDE_SCOPE, TAXONOMY_GAP, UNRESOLVED)
    NON_DOMAIN_OUTCOMES = {"OUTSIDE_SCOPE", "TAXONOMY_GAP", "UNRESOLVED"}

    def is_eligible_automated(record):
        """Automated system said ELIGIBLE (intake_status == ELIGIBLE)."""
        return record["automated_intake_status"] == "ELIGIBLE"

    def is_eligible_custodian(record):
        """Custodian classified as a known frozen domain."""
        return record["custodian_classification"] not in NON_DOMAIN_OUTCOMES

    # Compute confusion matrix
    tp = fp = fn = tn = 0
    per_domain_errors = defaultdict(list)
    disagreements = []

    for r in matched:
        a_eligible = is_eligible_automated(r)
        c_eligible = is_eligible_custodian(r)

        if a_eligible and c_eligible:
            tp += 1
            # Check domain agreement
            if r["automated_canonical_domain"] != r["custodian_classification"]:
                per_domain_errors["DOMAIN_MISMATCH"].append({
                    "source_id": r["source_id"],
                    "automated": r["automated_canonical_domain"],
                    "custodian": r["custodian_classification"],
                })
        elif a_eligible and not c_eligible:
            fp += 1
            disagreements.append({
                "source_id": r["source_id"],
                "type": "FALSE_POSITIVE",
                "automated": f"ELIGIBLE ({r['automated_canonical_domain']})",
                "custodian": r["custodian_classification"],
                "rationale": r["custodian_rationale"][:100],
            })
        elif not a_eligible and c_eligible:
            fn += 1
            disagreements.append({
                "source_id": r["source_id"],
                "type": "FALSE_NEGATIVE",
                "automated": f"FLAGGED ({r['automated_domain']})",
                "custodian": r["custodian_classification"],
                "rationale": r["custodian_rationale"][:100],
            })
        else:
            tn += 1
            # Both said not eligible — check if they agree on WHY
            auto_reason = "FLAGGED" if r["automated_intake_status"] == "FLAGGED" else r["automated_intake_status"]
            cust_reason = r["custodian_classification"]
            if auto_reason != cust_reason:
                per_domain_errors["REASON_MISMATCH"].append({
                    "source_id": r["source_id"],
                    "automated": f"{r['automated_intake_status']} ({r['automated_domain']})",
                    "custodian": cust_reason,
                })

    n = len(matched)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    accuracy = (tp + tn) / n if n > 0 else 0.0
    agreement = accuracy

    # Taxonomy gap rate
    taxonomy_gaps = sum(1 for r in matched if r["custodian_classification"] == "TAXONOMY_GAP")
    taxonomy_gap_rate = taxonomy_gaps / n if n > 0 else 0.0

    # Per-domain analysis
    custodian_domain_counts = Counter(r["custodian_classification"] for r in matched)

    # Build report
    report = {
        "report_type": "CROSS_VALIDATION_CONFUSION_MATRIX_V1",
        "report_version": "1.0.0",
        "generated_at": "2026-08-11T00:00:00Z",
        "custodian_adjudication_source": str(custodian_result_path),
        "custodian_blinding_status": custodian_data.get("blinding_status", "UNKNOWN"),
        "custodian_automated_fields_seen": custodian_data.get("automated_fields_seen", "UNKNOWN"),
        "n_records": n,
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "accuracy": round(accuracy, 4),
            "overall_agreement": round(agreement, 4),
        },
        "taxonomy_gap": {
            "count": taxonomy_gaps,
            "rate": round(taxonomy_gap_rate, 4),
        },
        "custodian_classification_distribution": dict(custodian_domain_counts.most_common()),
        "per_domain_errors": {k: v for k, v in per_domain_errors.items()},
        "disagreements": disagreements,
        "interpretation": {
            "precision_meaning": f"Of {tp+fp} records the automated system classified as eligible, "
                                 f"{tp} ({precision:.1%}) were confirmed by the custodian.",
            "recall_meaning": f"Of {tp+fn} records the custodian classified as eligible, "
                              f"the automated system found {tp} ({recall:.1%}).",
            "fpr_meaning": f"Of {fp+tn} records the custodian said are NOT eligible, "
                           f"the automated system incorrectly admitted {fp} ({fpr:.1%}).",
            "fnr_meaning": f"Of {fn+tp} records the custodian said ARE eligible, "
                           f"the automated system missed {fn} ({fnr:.1%}).",
            "accuracy_meaning": f"Overall agreement: {accuracy:.1%} of {n} records.",
        },
        "note": "This is the FIRST blinded cross-validation of the intake classifier. "
                "The custodian adjudicated independently without seeing automated fields. "
                "No source pairs constructed. No benchmark. No TEE. No taxonomy changes.",
    }

    # Save
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print()
    print("=== CROSS-VALIDATION CONFUSION MATRIX ===")
    print()
    print(f"Records: {n}")
    print(f"Custodian blinding: {custodian_data.get('blinding_status', '?')}")
    print(f"Automated fields seen by custodian: {custodian_data.get('automated_fields_seen', '?')}")
    print()
    cm = report["confusion_matrix"]
    print(f"Confusion Matrix (eligible = positive class):")
    print(f"  True Positive:  {tp}  (automated eligible + custodian eligible)")
    print(f"  False Positive: {fp}  (automated eligible + custodian NOT eligible)")
    print(f"  False Negative: {fn}  (automated NOT eligible + custodian eligible)")
    print(f"  True Negative:  {tn}  (automated NOT eligible + custodian NOT eligible)")
    print()
    print(f"Precision: {cm['precision']:.1%} — of automated-eligible, {tp}/{tp+fp} confirmed")
    print(f"Recall:    {cm['recall']:.1%} — of custodian-eligible, {tp}/{tp+fn} found by automated")
    print(f"FPR:       {cm['false_positive_rate']:.1%} — automated admitted {fp}/{fp+tn} that shouldn't be")
    print(f"FNR:       {cm['false_negative_rate']:.1%} — automated missed {fn}/{fn+tp} that should be eligible")
    print(f"Accuracy:  {cm['accuracy']:.1%} — overall agreement")
    print()
    print(f"Taxonomy gaps: {taxonomy_gaps} ({taxonomy_gap_rate:.1%})")
    print()
    print(f"Custodian classification distribution:")
    for cls, count in custodian_domain_counts.most_common():
        print(f"  {cls}: {count}")
    print()
    print(f"Disagreements: {len(disagreements)}")
    for d in disagreements:
        print(f"  {d['type']}: {d['source_id']}")
        print(f"    Automated: {d['automated']}")
        print(f"    Custodian: {d['custodian']}")
    print()
    print(f"Report saved: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--custodian", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    compute_cross_validation_analysis(
        custodian_result_path=Path(args.custodian),
        intake_manifest_path=Path(args.manifest),
        output_path=Path(args.output),
    )
