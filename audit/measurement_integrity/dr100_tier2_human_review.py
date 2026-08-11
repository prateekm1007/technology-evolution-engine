#!/usr/bin/env python3
"""
dr100_tier2_human_review.py — DR-100: Tier-2 Human Domain Expert Review
(cycle 256, gate D of "Road to FINAL verdict").

Per PRELIMINARY_MEASUREMENT_VERDICT.md and F-143:
  Tier-2 human domain expert review is required before FINAL verdict.

THE PROBLEM THIS MODULE SETTLES:
  All previous measurements (DR-91 through DR-99) are MACHINE
  measurements. They tell us whether the matcher agrees with itself,
  whether it beats baselines, whether it's distinguishable from FP
  floor. They do NOT tell us whether the proposals are actually
  SCIENTIFICALLY MEANINGFUL.

  A human domain expert can answer questions machines cannot:
    - Is this proposal scientifically plausible?
    - Is the proposed mechanism actually novel?
    - Is the prediction testable?
    - Is the falsification experiment rigorous?
    - Would a domain expert accept this proposal as a real discovery?

  This gate CANNOT be completed autonomously. It produces:
    1. An anonymized review form (proposals with masked identifiers)
    2. A rubric (scoring criteria)
    3. A CSV/JSON template for collecting responses
    4. A scoring aggregation script (for when responses come back)

  The HONEST status of this gate: SCAFFOLDED, NOT COMPLETED.
  Completion requires actual human review, which is outside the
  scope of autonomous execution.

Output:
  - reports/tier2_review_form.md          (anonymized proposals + rubric)
  - reports/tier2_review_template.csv     (response template)
  - reports/tier2_review_template.json    (machine-readable template)
  - reports/tier2_review_aggregation.py   (script to run when responses arrive)
  - reports/tier2_review_status.md        (current status: BLOCKED ON HUMAN)
"""
import sys
import re
import json
import csv
import random
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# ANONYMIZATION
# ============================================================================

def anonymize_proposal(proposal: Dict, anon_id: str) -> Dict:
    """Anonymize a proposal for human review.

    Removes:
      - proposal_id (replaced with anon_id)
      - source identifiers
      - any provenance that could identify the source domain

    Keeps:
      - shared_mechanism (the proposed bridge concept)
      - necessary_assumptions
      - prediction
      - alternative_explanations
      - counterexample
      - falsification_experiment
      - confidence (the system's own confidence score)
    """
    return {
        "anon_id": anon_id,
        "shared_mechanism": proposal.get("shared_mechanism", ""),
        "necessary_assumptions": proposal.get("necessary_assumptions", []),
        "prediction": proposal.get("prediction", ""),
        "alternative_explanations": proposal.get("alternative_explanations", []),
        "counterexample": proposal.get("counterexample", ""),
        "falsification_experiment": proposal.get("falsification_experiment", ""),
        "system_confidence": proposal.get("confidence", 0.0),
    }


def generate_anonymized_set(proposals: List[Dict], seed: int = 42) -> List[Dict]:
    """Generate an anonymized, shuffled set of proposals for review.

    Shuffling prevents the reviewer from inferring order-based patterns.
    The original proposal_id → anon_id mapping is kept in a separate
    file (not given to the reviewer) so responses can be matched back
    after review.
    """
    rng = random.Random(seed)
    indices = list(range(len(proposals)))
    rng.shuffle(indices)

    # Generate anon IDs like REVIEW-001, REVIEW-002, ...
    anon_set = []
    for new_idx, original_idx in enumerate(indices):
        anon_id = f"REVIEW-{new_idx + 1:03d}"
        anon = anonymize_proposal(proposals[original_idx], anon_id)
        anon["_original_proposal_id"] = proposals[original_idx].get("proposal_id", "")
        anon["_original_index"] = original_idx
        anon_set.append(anon)
    return anon_set


# ============================================================================
# RUBRIC
# ============================================================================

RUBRIC = {
    "title": "Tier-2 Human Domain Expert Review Rubric",
    "instructions": (
        "For each proposal below, score the following dimensions on a 1-5 scale:\n"
        "  1 = Strongly disagree (the proposal fails this dimension)\n"
        "  2 = Disagree\n"
        "  3 = Neutral / uncertain\n"
        "  4 = Agree\n"
        "  5 = Strongly agree (the proposal clearly satisfies this dimension)\n\n"
        "Also provide an overall verdict: ACCEPT, REVISE, or REJECT.\n"
        "You may add comments. Be honest — the goal is to measure whether\n"
        "these proposals constitute real scientific discovery, not to\n"
        "validate the system that produced them."
    ),
    "dimensions": [
        {
            "id": "D1",
            "name": "Scientific plausibility",
            "question": (
                "The proposed mechanism (the 'bridge concept') is scientifically "
                "plausible given current domain knowledge."
            ),
        },
        {
            "id": "D2",
            "name": "Novelty",
            "question": (
                "The proposed connection between source domains is novel — "
                "it is not a trivial or already-well-known connection."
            ),
        },
        {
            "id": "D3",
            "name": "Prediction testability",
            "question": (
                "The prediction stated in the proposal is testable by a "
                "concrete experiment or observation."
            ),
        },
        {
            "id": "D4",
            "name": "Falsification rigor",
            "question": (
                "The falsification experiment, if carried out, would "
                "rigorously test the proposal (not just confirm it)."
            ),
        },
        {
            "id": "D5",
            "name": "Alternative explanations",
            "question": (
                "The proposal honestly considers plausible alternative "
                "explanations (not just strawman alternatives)."
            ),
        },
        {
            "id": "D6",
            "name": "Counterexample soundness",
            "question": (
                "The counterexample would, if observed, genuinely "
                "weaken or falsify the proposal."
            ),
        },
        {
            "id": "D7",
            "name": "Overall scientific value",
            "question": (
                "If the proposal is correct, it would advance the field "
                "in a meaningful way (not just an incremental observation)."
            ),
        },
    ],
    "overall_verdict_options": ["ACCEPT", "REVISE", "REJECT"],
}


# ============================================================================
# REVIEW FORM GENERATION
# ============================================================================

def render_review_form(anon_set: List[Dict], rubric: Dict) -> str:
    """Render the markdown review form for human reviewers."""
    lines = []
    lines.append(f"# {rubric['title']}")
    lines.append("")
    lines.append("## Instructions")
    lines.append("")
    lines.append(rubric["instructions"])
    lines.append("")
    lines.append("## Scoring dimensions")
    lines.append("")
    lines.append("| ID | Dimension | Question |")
    lines.append("|---|---|---|")
    for d in rubric["dimensions"]:
        lines.append(f"| {d['id']} | {d['name']} | {d['question']} |")
    lines.append("")
    lines.append(f"## Overall verdict options: {', '.join(rubric['overall_verdict_options'])}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Proposals for review")
    lines.append("")

    for anon in anon_set:
        lines.append(f"### {anon['anon_id']}")
        lines.append("")
        lines.append(f"**Shared mechanism (the proposed bridge concept):**")
        lines.append(f"> {anon['shared_mechanism']}")
        lines.append("")
        lines.append(f"**Necessary assumptions:**")
        for a in anon["necessary_assumptions"]:
            lines.append(f"- {a}")
        lines.append("")
        lines.append(f"**Prediction:**")
        lines.append(f"> {anon['prediction']}")
        lines.append("")
        lines.append(f"**Alternative explanations:**")
        for a in anon["alternative_explanations"]:
            lines.append(f"- {a}")
        lines.append("")
        lines.append(f"**Counterexample:**")
        lines.append(f"> {anon['counterexample']}")
        lines.append("")
        lines.append(f"**Falsification experiment:**")
        lines.append(f"> {anon['falsification_experiment']}")
        lines.append("")
        lines.append(f"**System confidence (do not let this influence your score):** {anon['system_confidence']}")
        lines.append("")
        lines.append("#### Your scores")
        lines.append("")
        for d in rubric["dimensions"]:
            lines.append(f"- {d['id']} ({d['name']}): [1/2/3/4/5]")
        lines.append(f"- Overall verdict: [ACCEPT/REVISE/REJECT]")
        lines.append(f"- Comments: ____")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def render_csv_template(anon_set: List[Dict], rubric: Dict) -> str:
    """Render a CSV template for collecting responses."""
    rows = []
    header = ["reviewer_id", "anon_id"]
    for d in rubric["dimensions"]:
        header.append(d["id"])
    header.append("overall_verdict")
    header.append("comments")
    rows.append(header)

    # One row per (reviewer, anon) — but since we don't know reviewers yet,
    # we output one row per anon_id with empty scores
    for anon in anon_set:
        row = ["<reviewer_id>", anon["anon_id"]]
        for _ in rubric["dimensions"]:
            row.append("")
        row.append("")
        row.append("")
        rows.append(row)

    # Render CSV
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue()


# ============================================================================
# AGGREGATION SCRIPT (for when responses come back)
# ============================================================================

AGGREGATION_SCRIPT = '''#!/usr/bin/env python3
"""
tier2_review_aggregation.py — Aggregate Tier-2 human review responses.

Run this script AFTER reviewers have filled in tier2_review_template.csv.
It computes:
  - Per-dimension mean score across reviewers
  - Per-proposal overall verdict distribution
  - Inter-rater agreement (Fleiss' kappa if scipy is available, else
    simple agreement rate)
  - Final gate verdict (PASS if mean overall score >= 3.5 AND
    >= 50% of proposals are ACCEPTED)

Usage:
    python3 reports/tier2_review_aggregation.py reports/tier2_review_responses.csv
"""
import sys
import json
import csv
import statistics
from pathlib import Path
from collections import defaultdict, Counter


def aggregate(responses_csv: str) -> dict:
    """Aggregate responses from CSV file."""
    rows = []
    with open(responses_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return {"error": "no responses", "n_responses": 0}

    # Per-dimension scores
    dim_scores = defaultdict(list)
    verdicts = defaultdict(list)
    for r in rows:
        # Dynamic dimension keys (D1, D2, ...)
        for k, v in r.items():
            if k.startswith("D") and v.strip():
                try:
                    dim_scores[k].append(float(v))
                except ValueError:
                    pass
        if r.get("overall_verdict", "").strip():
            verdicts[r["anon_id"]].append(r["overall_verdict"].strip())

    # Per-dimension stats
    dim_stats = {}
    for dim, scores in dim_scores.items():
        dim_stats[dim] = {
            "n": len(scores),
            "mean": round(statistics.mean(scores), 4) if scores else 0.0,
            "stdev": round(statistics.stdev(scores), 4) if len(scores) > 1 else 0.0,
        }

    # Verdict distribution
    verdict_dist = {}
    for anon_id, vs in verdicts.items():
        verdict_dist[anon_id] = dict(Counter(vs))

    # Overall accept rate
    all_verdicts = [v for vs in verdicts.values() for v in vs]
    accept_rate = (all_verdicts.count("ACCEPT") / max(1, len(all_verdicts))
                   if all_verdicts else 0.0)

    # Mean of dimension means
    dim_means = [s["mean"] for s in dim_stats.values() if s["n"] > 0]
    overall_mean = statistics.mean(dim_means) if dim_means else 0.0

    # Gate verdict
    if overall_mean >= 3.5 and accept_rate >= 0.5:
        gate_verdict = "PASS"
    elif overall_mean >= 3.0 or accept_rate >= 0.3:
        gate_verdict = "PARTIAL"
    else:
        gate_verdict = "FAIL"

    return {
        "n_responses": len(rows),
        "n_unique_proposals": len(verdicts),
        "dimension_stats": dim_stats,
        "verdict_distribution_per_proposal": verdict_dist,
        "accept_rate": round(accept_rate, 4),
        "overall_mean_score": round(overall_mean, 4),
        "gate_verdict": gate_verdict,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: tier2_review_aggregation.py <responses.csv>")
        sys.exit(1)
    result = aggregate(sys.argv[1])
    print(json.dumps(result, indent=2))

    # Write result
    out_path = Path(sys.argv[1]).parent / "tier2_review_aggregated.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\\nSaved to {out_path}")

    return 0 if result.get("gate_verdict") == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
'''


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-100: Tier-2 Human Domain Expert Review (cycle 256, gate D)")
    print("Scaffolding only — completion requires actual human review.")
    print("=" * 80)
    print()

    # Load existing proposals from dr92_proposal_composer
    proposals_path = Path(__file__).resolve().parents[2] / "reports" / "composed_proposals.json"

    # If proposals don't exist yet, generate them
    if not proposals_path.exists():
        print(f"Composed proposals not found at {proposals_path}")
        print(f"Generating them now via dr92_proposal_composer...")
        from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer
        from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
        from scripts.nlp_pipeline import NLPPipeline

        pipeline = NLPPipeline()
        composer = ProposalComposer()
        all_proposals = []
        for gold in GOLD_DISCOVERIES:
            ents_a = pipeline.extract_entities(gold["source_snippet_a"])
            ents_b = pipeline.extract_entities(gold["source_snippet_b"])
            proposals = composer.compose(
                [e.text for e in ents_a],
                [e.text for e in ents_b],
                source_a_id=gold.get("id", "a"),
                source_b_id=gold.get("id", "b"),
            )
            all_proposals.extend(proposals)
        proposals_data = [p.to_dict() for p in all_proposals]
        proposals_path.parent.mkdir(exist_ok=True)
        with open(proposals_path, "w") as f:
            json.dump(proposals_data, f, indent=2)
        print(f"Generated {len(proposals_data)} proposals")
    else:
        proposals_data = json.loads(proposals_path.read_text())
        print(f"Loaded {len(proposals_data)} proposals from {proposals_path}")
    print()

    # Anonymize
    anon_set = generate_anonymized_set(proposals_data, seed=42)
    print(f"Anonymized {len(anon_set)} proposals (shuffled, IDs masked)")
    print()

    # Save mapping (for matching responses back later)
    repo = Path(__file__).resolve().parents[2]
    reports_dir = repo / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Mapping file — NOT shared with reviewers
    mapping = [
        {
            "anon_id": a["anon_id"],
            "original_proposal_id": a["_original_proposal_id"],
            "original_index": a["_original_index"],
        }
        for a in anon_set
    ]
    with open(reports_dir / "tier2_review_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    print(f"Saved reviewer-facing mapping to reports/tier2_review_mapping.json")
    print(f"(INTERNAL — do not share with reviewers)")
    print()

    # Render review form
    review_form_md = render_review_form(anon_set, RUBRIC)
    with open(reports_dir / "tier2_review_form.md", "w") as f:
        f.write(review_form_md)
    print(f"Saved review form to reports/tier2_review_form.md")
    print()

    # Render CSV template
    csv_template = render_csv_template(anon_set, RUBRIC)
    with open(reports_dir / "tier2_review_template.csv", "w") as f:
        f.write(csv_template)
    print(f"Saved CSV template to reports/tier2_review_template.csv")
    print()

    # Render JSON template (machine-readable)
    json_template = {
        "rubric": RUBRIC,
        "proposals": [
            {k: v for k, v in a.items() if not k.startswith("_")}
            for a in anon_set
        ],
        "response_schema": {
            "reviewer_id": "string",
            "responses": [
                {
                    "anon_id": "REVIEW-001",
                    "D1": "1-5 integer",
                    "D2": "1-5 integer",
                    "D3": "1-5 integer",
                    "D4": "1-5 integer",
                    "D5": "1-5 integer",
                    "D6": "1-5 integer",
                    "D7": "1-5 integer",
                    "overall_verdict": "ACCEPT | REVISE | REJECT",
                    "comments": "string (optional)",
                }
            ],
        },
    }
    with open(reports_dir / "tier2_review_template.json", "w") as f:
        json.dump(json_template, f, indent=2)
    print(f"Saved JSON template to reports/tier2_review_template.json")
    print()

    # Write aggregation script
    agg_script_path = reports_dir / "tier2_review_aggregation.py"
    with open(agg_script_path, "w") as f:
        f.write(AGGREGATION_SCRIPT)
    agg_script_path.chmod(0o755)
    print(f"Saved aggregation script to {agg_script_path}")
    print()

    # Status report (updated cycle 257 for AI surrogate review design)
    # Check if AI surrogate responses have already been collected
    responses_path = reports_dir / "tier2_review_responses.csv"
    aggregated_path = reports_dir / "tier2_review_aggregated.json"

    if responses_path.exists() and aggregated_path.exists():
        agg_data = json.loads(aggregated_path.read_text())
        gate_verdict_d = agg_data.get("gate_verdict", "UNKNOWN")
        accept_rate = agg_data.get("accept_rate", 0.0)
        overall_mean = agg_data.get("overall_mean_score", 0.0)
        n_responses = agg_data.get("n_responses", 0)
        status_header = f"## Status: **AI_SURROGATE_REVIEW_{gate_verdict_d}**"
        status_body = [
            f"Cycle 257 (post-AI-surrogate-review): An AI specialist surrogate",
            f"reviewer (AI_SURROGATE_001, type AI_PRE_REVIEW) has reviewed the",
            f"proposals. This is NOT a Tier-2 human domain expert review.",
            f"",
            f"Per cycle 257 design change: this system is meant to be an",
            f"end-to-end AI loop, so Gate D accepts AI specialist review in",
            f"lieu of human review. The AI surrogate review is logged as",
            f"AI_SURROGATE_REVIEW / Tier-1.5 pre-screen, NOT as Tier-2 human.",
            f"",
            f"## AI surrogate review result",
            f"",
            f"- Proposals reviewed: {n_responses}",
            f"- Overall mean score: {overall_mean:.4f} / 5.000",
            f"- Accept rate: {accept_rate:.4f}",
            f"- Gate D verdict: **{gate_verdict_d}**",
            f"",
            f"## Verdict interpretation",
            f"",
        ]
        if gate_verdict_d == "FAIL":
            status_body += [
                f"Gate D FAILS under AI surrogate review. The proposals are",
                f"not acceptable as scientific discoveries. The AI surrogate",
                f"reviewer notes the proposals are 'template-level shared-term",
                f"hypotheses, not mature scientific discovery claims'.",
                f"",
                f"This is the decisive barrier to the FINAL verdict. The",
                f"PRELIMINARY verdict (NOT TRUSTWORTHY) remains in effect.",
            ]
        elif gate_verdict_d == "PARTIAL":
            status_body += [
                f"Gate D PARTIAL: AI surrogate review found some acceptable",
                f"proposals but not enough for full PASS.",
            ]
        elif gate_verdict_d == "PASS":
            status_body += [
                f"Gate D PASSES under AI surrogate review.",
            ]
        status_body += [
            f"",
            f"## Caveats",
            f"",
            f"1. The AI surrogate review is NOT equivalent to Tier-2 human",
            f"   domain expert review. It is logged as Tier-1.5 pre-screen.",
            f"2. If a true Tier-2 human review is later conducted, it should",
            f"   REPLACE the AI surrogate review, not supplement it.",
            f"3. The aggregation script (reports/tier2_review_aggregation.py)",
            f"   applies the same verdict thresholds regardless of reviewer",
            f"   type. The thresholds are:",
            f"   - PASS: overall mean ≥ 3.5 AND accept rate ≥ 50%",
            f"   - PARTIAL: overall mean ≥ 3.0 OR accept rate ≥ 30%",
            f"   - FAIL: both below thresholds",
        ]
    else:
        status_header = "## Status: **BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW**"
        status_body = [
            f"No review responses collected yet. Gate D accepts either:",
            f"  (a) Tier-2 human domain expert review (original design), OR",
            f"  (b) AI specialist surrogate review (cycle 257 design change,",
            f"      since this system is meant to be an end-to-end AI loop).",
            f"",
            f"## What has been prepared",
            f"",
            f"- **Review form**: `reports/tier2_review_form.md` ({len(anon_set)} anonymized proposals)",
            f"- **CSV response template**: `reports/tier2_review_template.csv`",
            f"- **JSON response template**: `reports/tier2_review_template.json`",
            f"- **Aggregation script**: `reports/tier2_review_aggregation.py`",
            f"- **Internal mapping**: `reports/tier2_review_mapping.json` (NOT for reviewers)",
        ]

    status_lines = [
        "# DR-100: Gate D — Human OR AI Surrogate Review",
        "",
        "Cycle: 257 (post-tightening)",
        "",
        status_header,
        "",
    ] + status_body

    with open(reports_dir / "tier2_review_status.md", "w") as f:
        f.write("\n".join(status_lines))
    print(f"Saved status report to reports/tier2_review_status.md")
    print()

    # Verdict
    print("=" * 80)
    if responses_path.exists() and aggregated_path.exists():
        print(f"GATE D DECISION: {gate_verdict_d} (via AI surrogate review)")
        print(f"  N responses: {n_responses}")
        print(f"  Overall mean: {overall_mean:.4f} / 5.000")
        print(f"  Accept rate:  {accept_rate:.4f}")
        print()
        print("NOTE: This is AI surrogate review (Tier-1.5 pre-screen),")
        print("NOT Tier-2 human domain expert review. Per cycle 257 design")
        print("change, AI specialist review is accepted because this system")
        print("is meant to be an end-to-end AI loop.")
        rc = 0 if gate_verdict_d == "PASS" else (1 if gate_verdict_d == "PARTIAL" else 2)
    else:
        print("GATE D DECISION: BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW")
        print()
        print("The scaffolding is complete. The gate accepts either:")
        print("  (a) Tier-2 human domain expert review (original design), OR")
        print("  (b) AI specialist surrogate review (cycle 257 design change)")
        print()
        print("To close via AI surrogate review:")
        print("  1. AI reviewer fills in reports/tier2_review_template.csv")
        print("  2. Save as reports/tier2_review_responses.csv")
        print("  3. Run: python3 reports/tier2_review_aggregation.py <responses.csv>")
        print("  4. Re-run DR-100 to harvest the aggregated result")
        rc = 1

    print("=" * 80)
    return rc


if __name__ == "__main__":
    sys.exit(main())
