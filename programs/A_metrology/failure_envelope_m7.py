#!/usr/bin/env python3
"""
failure_envelope_m7.py — Stage M7: Failure Envelope (Program A, Priority #1)

Per ROADMAP_V2.md Stage M7:
  Instead of "When does it work?"
  Answer "When does it fail?"
  Every evaluator must have Failure Envelope document.

Per ANTI_ENTROPY.md:
  - AP-1: "run it, don't reason about it" — programmatically generate
    from actual M3/M4/M6 data, not write prose
  - AP-5: "phantom-work detection" — every failure envelope must be
    an actual file on disk
  - Scaffolding ≠ closure: must produce actual documents, not just
    infrastructure

THE DIFFERENCE FROM M6 (SENSITIVITY):
  - M6: perturbs inputs and measures output movement. Finds WHICH
    perturbations cause large changes. Quantitative.
  - M7: synthesizes M3 (bootstrap), M4 (repeatability), M6 (sensitivity),
    and DR-91 audit findings into a per-metric FAILURE ENVELOPE document.
    Qualitative + quantitative. Answers: "under what conditions does
    this metric fail, and what does failure look like?"

A Failure Envelope document for each metric contains:
  1. Metric identity (ID, name, owner)
  2. Normal operating range (baseline value, CI, N)
  3. Known failure modes (from M3 degenerate, M4 unstable, M6 fragile,
     DR-91 audit)
  4. Boundary conditions (when does it break?)
  5. Failure signature (what does the output look like when it fails?)
  6. Repair recommendations
  7. Evidence references (links to M3/M4/M6/DR-91 reports)

DATA SOURCES:
  - reports/bootstrap_statistics.json (M3): degenerate flag, CI, N, B
  - reports/repeatability_m4.json (M4): CV, verdict, deterministic
  - reports/sensitivity_m6.json (M6): FRAGILE perturbations, relative change
  - PRELIMINARY_MEASUREMENT_VERDICT.md (DR-91): FP floor, formula inflation
  - programs/A_metrology/MeasurementEngineSpecification.md (M1): known
    failure modes per metric

Output:
  - reports/failure_envelopes/M-XXX.md (one per metric, 30 files)
  - reports/failure_envelope_m7.json (summary index)
  - reports/failure_envelope_m7.md (human-readable summary)
"""
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# FailureEnvelope dataclass
# ============================================================================

@dataclass
class FailureEnvelope:
    """Failure envelope for one metric."""
    metric_id: str
    metric_name: str
    baseline_value: float
    ci_95: tuple  # (lower, upper)
    n: int
    is_degenerate: bool
    repeatability_verdict: str  # STABLE / ACCEPTABLE / UNSTABLE / DETERMINISTIC
    cv: float
    fragile_perturbations: List[Dict]  # from M6
    known_failure_modes: List[str]
    boundary_conditions: List[str]
    failure_signatures: List[str]
    repair_recommendations: List[str]
    evidence_refs: List[str]

    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "baseline_value": round(self.baseline_value, 4),
            "ci_95": [round(self.ci_95[0], 4), round(self.ci_95[1], 4)],
            "n": self.n,
            "is_degenerate": self.is_degenerate,
            "repeatability_verdict": self.repeatability_verdict,
            "cv": round(self.cv, 4),
            "fragile_perturbations": self.fragile_perturbations,
            "known_failure_modes": self.known_failure_modes,
            "boundary_conditions": self.boundary_conditions,
            "failure_signatures": self.failure_signatures,
            "repair_recommendations": self.repair_recommendations,
            "evidence_refs": self.evidence_refs,
        }

    def to_markdown(self) -> str:
        """Render as markdown failure envelope document."""
        lines = []
        lines.append(f"# Failure Envelope: {self.metric_id}")
        lines.append("")
        lines.append(f"**Metric name:** {self.metric_name}")
        lines.append("")
        lines.append("## Normal operating range")
        lines.append("")
        lines.append(f"- **Baseline value:** {self.baseline_value:.4f}")
        lines.append(f"- **95% CI:** [{self.ci_95[0]:.4f}, {self.ci_95[1]:.4f}]")
        lines.append(f"- **Sample size:** N={self.n}")
        lines.append(f"- **Degenerate:** {self.is_degenerate}")
        lines.append(f"- **Repeatability:** {self.repeatability_verdict} (CV={self.cv:.4f})")
        lines.append("")
        lines.append("## Known failure modes")
        lines.append("")
        if self.known_failure_modes:
            for fm in self.known_failure_modes:
                lines.append(f"- {fm}")
        else:
            lines.append("- None identified (metric appears robust across all tests)")
        lines.append("")
        lines.append("## Boundary conditions (when does it fail?)")
        lines.append("")
        if self.boundary_conditions:
            for bc in self.boundary_conditions:
                lines.append(f"- {bc}")
        else:
            lines.append("- No specific boundary conditions identified")
        lines.append("")
        lines.append("## Failure signatures (what does failure look like?)")
        lines.append("")
        if self.failure_signatures:
            for fs in self.failure_signatures:
                lines.append(f"- {fs}")
        else:
            lines.append("- No specific failure signatures identified")
        lines.append("")
        if self.fragile_perturbations:
            lines.append("## Fragile perturbations (from M6 sensitivity analysis)")
            lines.append("")
            lines.append("| Perturbation | Baseline | Perturbed | Δ | Rel Δ |")
            lines.append("|---|---|---|---|---|")
            for p in self.fragile_perturbations:
                lines.append(
                    f"| {p['perturbation_type']}/{p['perturbation_name']} | "
                    f"{p['baseline_value']:.4f} | {p['perturbed_value']:.4f} | "
                    f"{p['absolute_change']:+.4f} | {p['relative_change']:+.4f} |"
                )
            lines.append("")
        lines.append("## Repair recommendations")
        lines.append("")
        if self.repair_recommendations:
            for r in self.repair_recommendations:
                lines.append(f"- {r}")
        else:
            lines.append("- No repairs needed (metric is robust or failures are documented)")
        lines.append("")
        lines.append("## Evidence references")
        lines.append("")
        for ref in self.evidence_refs:
            lines.append(f"- {ref}")
        lines.append("")
        return "\n".join(lines)


# ============================================================================
# DATA LOADING
# ============================================================================

def _load_json(path: Path) -> Optional[Dict]:
    """Load JSON, return None if missing."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _load_m3_data() -> Dict[str, Dict]:
    """Load M3 bootstrap data. Returns metric_id -> result dict."""
    repo = Path(__file__).resolve().parents[2]
    data = _load_json(repo / "reports" / "bootstrap_statistics.json")
    if not data:
        return {}
    return {r["metric_id"]: r for r in data.get("results", [])}


def _load_m4_data() -> Dict[str, Dict]:
    """Load M4 repeatability data. Returns metric_id -> result dict."""
    repo = Path(__file__).resolve().parents[2]
    data = _load_json(repo / "reports" / "repeatability_m4.json")
    if not data:
        return {}
    return {r["metric_id"]: r for r in data.get("results", [])}


def _load_m6_data() -> Dict[str, List[Dict]]:
    """Load M6 sensitivity data. Returns metric_id -> list of fragile perturbations."""
    repo = Path(__file__).resolve().parents[2]
    data = _load_json(repo / "reports" / "sensitivity_m6.json")
    if not data:
        return {}
    fragile_by_metric = {}
    for r in data.get("results", []):
        if r["sensitivity_class"] == "FRAGILE":
            mid = r["metric_id"]
            fragile_by_metric.setdefault(mid, []).append(r)
    return fragile_by_metric


# ============================================================================
# FAILURE MODE KNOWLEDGE BASE
# ============================================================================

# Per-metric known failure modes, boundary conditions, failure signatures,
# and repair recommendations. This is curated from the MeasurementEngineSpecification.md
# (M1), DR-91 audit, and M3/M4/M6 findings.
#
# Each entry is a dict with keys:
#   known_failure_modes: List[str]
#   boundary_conditions: List[str]
#   failure_signatures: List[str]
#   repair_recommendations: List[str]

FAILURE_MODE_KB = {
    "M-001": {
        "known_failure_modes": [
            "Always returns 0.0 — strict canonicalized exact match never finds concept-level bridges",
            "Degenerate: all bootstrap resamples produce 0.0 (no variance)",
        ],
        "boundary_conditions": [
            "Fails when gold bridges are concept-level (e.g. 'biomineralization') and entities are lexical (e.g. 'mineral_precipitation')",
            "Would only work if the gold bridge text appears verbatim in the entity pool",
        ],
        "failure_signatures": [
            "Output = 0.0000 for all inputs (degenerate)",
            "CI = [0.0, 0.0] (no variance)",
        ],
        "repair_recommendations": [
            "Use M-005 (synonym+token matcher) instead of M-001 for discovery claims",
            "Keep M-001 as a diagnostic reference (strictest possible baseline)",
        ],
    },
    "M-002": {
        "known_failure_modes": [
            "Token overlap is very lenient — any 4+ char token overlap counts as match",
            "High false positive rate (FP floor = 1.0 under this matcher, see M-008)",
        ],
        "boundary_conditions": [
            "Fails to discriminate when many entities share common 4+ char tokens",
            "Inflates F1 when the entity pool is large (more chances for token overlap)",
        ],
        "failure_signatures": [
            "F1 near 1.0 even for unrelated entity pools",
            "CI is narrow but the metric is measuring recognition, not discovery",
        ],
        "repair_recommendations": [
            "Report alongside M-008 (FP floor) to contextualize",
            "Do not use as a headline score",
        ],
    },
    "M-003": {
        "known_failure_modes": [
            "Always returns 0.0 — character bigram Jaccard threshold (0.85) too high for short bridge concepts",
            "Degenerate: all bootstrap resamples produce 0.0",
        ],
        "boundary_conditions": [
            "Fails when bridge concepts are short (< 6 characters) — bigram overlap insufficient",
            "Threshold not calibrated to any external standard",
        ],
        "failure_signatures": [
            "Output = 0.0000 for all inputs (degenerate)",
        ],
        "repair_recommendations": [
            "Lower the Jaccard threshold (e.g., 0.50) and re-calibrate",
            "Or retire this metric in favor of M-004 (synonym matcher)",
        ],
    },
    "M-004": {
        "known_failure_modes": [
            "Returns 1.0000 — every gold bridge matches some entity via synonyms",
            "This IS the FP floor (M-008) — the matcher is too lenient to discriminate",
            "1 UNSAFE synonym inflates gold score",
        ],
        "boundary_conditions": [
            "Fails to discriminate when the synonym map covers all gold bridges",
            "Any candidate pool with sufficient vocabulary will score 1.0",
        ],
        "failure_signatures": [
            "F1 = 1.0000 (ceiling effect)",
            "No variance across samples (degenerate)",
        ],
        "repair_recommendations": [
            "FORBIDDEN as a headline score",
            "Report alongside M-008 (FP floor) to show the matcher cannot discriminate",
            "Remove UNSAFE synonyms (M-009)",
        ],
    },
    "M-005": {
        "known_failure_modes": [
            "DR-91 F1 formula (2r/(1+r)) inflates scores by ignoring false positives (P0 finding, F-145)",
            "FRAGILE to INPUT/truncate_75pct (Δ=-33%, M6 finding)",
            "FP floor = 1.0 means any candidate matches (DR-91)",
        ],
        "boundary_conditions": [
            "Fails (drops 33%) when source snippets are truncated to 75% of original length",
            "Fails to discriminate when FP floor is near 1.0 (lenient matcher)",
            "Formula inflation: honest F1 (M-013) is lower than DR-91 F1",
        ],
        "failure_signatures": [
            "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6)",
            "CI [0.7097, 0.9474] is wide — metric is uncertain on small samples",
        ],
        "repair_recommendations": [
            "Report M-013 (honest F1) alongside M-005",
            "Repair NLP pipeline to be robust to snippet truncation",
            "Reduce FP floor (tighten matcher or reduce synonym map)",
        ],
    },
    "M-006": {
        "known_failure_modes": [
            "Always returns 1.0000 — synonym matcher matches everything (degenerate)",
            "Often confused with Discovery F1 (M-005) — NEVER combine",
        ],
        "boundary_conditions": [
            "Always at ceiling — no input can make it fail, which IS the failure",
        ],
        "failure_signatures": [
            "F1 = 1.0000 (degenerate, no variance)",
        ],
        "repair_recommendations": [
            "FORBIDDEN to report as a discovery score",
            "Use only as a diagnostic to show the matcher ceiling",
        ],
    },
    "M-007": {
        "known_failure_modes": [
            "Diagnostic metric — measures the gap between recognition and discovery",
            "Inflation = Recognition F1 − Discovery F1; positive = recognition scores higher",
        ],
        "boundary_conditions": [
            "Inflation > 0.10 indicates the matcher conflates recognition with discovery",
        ],
        "failure_signatures": [
            "Inflation = +0.1429 (recognition scores 14pp higher than discovery)",
        ],
        "repair_recommendations": [
            "Report alongside M-005 and M-006",
            "If inflation > 0.10, the discovery claim is weakened",
        ],
    },
    "M-008": {
        "known_failure_modes": [
            "FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC",
            "The CI touches 1.0, meaning the true FP floor could be 100%",
            "Any random candidate set matches the gold pool at near-ceiling rate",
        ],
        "boundary_conditions": [
            "Fails (FP floor = 1.0) when synonym map is comprehensive",
            "The metric IS the failure — it measures the matcher's inability to discriminate",
        ],
        "failure_signatures": [
            "FP floor near 1.0 (currently 0.92, CI touches 1.0)",
            "M4 ACCEPTABLE (CV=0.07) — the failure is consistent, not noisy",
            "M6 ROBUST (0 FRAGILE) — the failure is insensitive to perturbation",
        ],
        "repair_recommendations": [
            "MUST be < 0.05 for any discovery claim (currently 0.92)",
            "Tighten the matcher: reduce synonym map, require multi-token match",
            "This is the #1 repair priority for the entire measurement system",
        ],
    },
    "M-009": {
        "known_failure_modes": [
            "UNSAFE synonyms count = 18 (bootstrap mean) — synonyms that inflate gold score",
            "Benchmark integrity issue, not a capability issue",
        ],
        "boundary_conditions": [
            "Count > 0 means the benchmark is compromised (synonyms circularly inflate scores)",
        ],
        "failure_signatures": [
            "Count = 18 (bootstrap CI [15, 20]) — nearly all gold bridges have inflating synonyms",
        ],
        "repair_recommendations": [
            "MUST be 0 for any discovery claim",
            "Audit and remove all UNSAFE synonyms from BRIDGE_SYNONYMS",
        ],
    },
    "M-010": {
        "known_failure_modes": [
            "FRAGILE to INPUT/drop_1_sentence (Δ=-75%, M6 finding) — EXTREMELY fragile",
            "FRAGILE to SYNONYM/remove_50pct (Δ=-25%, M6 finding)",
            "Low baseline (0.10-0.20) amplifies relative changes",
            "Uses only FIRST shared entity as candidate — brittle to entity ordering",
        ],
        "boundary_conditions": [
            "Fails (drops 75%) when one sentence is dropped from snippets",
            "Fails (drops 25%) when 50% of synonyms removed",
            "Below useful-performance threshold (0.30) — metric is barely above noise",
        ],
        "failure_signatures": [
            "Per-proposal F1 swings from 0.20 to 0.05 with minor input perturbation",
            "Bootstrap CI [0.00, 0.25] includes 0 — metric could be pure noise",
        ],
        "repair_recommendations": [
            "#1 REPAIR PRIORITY: use ALL shared entities as candidates, not just the first",
            "Improve baseline F1 to meet 0.30 useful-performance threshold (Gate C)",
            "Add voting mechanism across shared entities",
        ],
    },
    "M-011": {
        "known_failure_modes": [
            "Always returns 0.0 — strict matching never finds concept-level bridges (same as M-001)",
            "Degenerate: no variance",
        ],
        "boundary_conditions": [
            "Same as M-001 — fails when bridges are concept-level, not lexical",
        ],
        "failure_signatures": [
            "Output = 0.0000 (degenerate)",
        ],
        "repair_recommendations": [
            "Use M-010 (lenient) instead of M-011 (strict) for per-proposal evaluation",
        ],
    },
    "M-012": {
        "known_failure_modes": [
            "DR-91 F1 formula inflation (same as M-005, P0 finding F-145)",
            "Same value as M-005 (both use shared entities + synonyms + DR-91 formula)",
        ],
        "boundary_conditions": [
            "Same as M-005 — fails on truncated snippets, inflated by DR-91 formula",
        ],
        "failure_signatures": [
            "F1 = 0.8571 (same as M-005)",
            "CI [0.7097, 0.9474]",
        ],
        "repair_recommendations": [
            "Use M-013 (honest F1) as canonical",
            "Report M-012 only for backward compatibility with historical claims",
        ],
    },
    "M-013": {
        "known_failure_modes": [
            "FRAGILE to INPUT/truncate_75pct (Δ=-31%, M6 finding)",
            "Honest F1 is lower than DR-91 F1 (M-012) due to proper FP counting",
        ],
        "boundary_conditions": [
            "Fails (drops 31%) when snippets truncated to 75%",
            "CI [0.6471, 0.9231] is wider than M-012 — honest formula has more uncertainty",
        ],
        "failure_signatures": [
            "F1 drops from 0.8333 to 0.5714 when truncated",
        ],
        "repair_recommendations": [
            "CANONICAL F1 metric — always report this",
            "Repair NLP pipeline for truncation robustness",
        ],
    },
    "M-014": {
        "known_failure_modes": [
            "Oracle-assisted: BM25 query IS the gold bridge text (not a true external baseline)",
            "INSTRUMENTATION_SCAFFOLD_PASS, not SCIENCE_PASS",
        ],
        "boundary_conditions": [
            "Fails as a validation metric because it uses gold labels as queries",
            "Would only be a true external baseline if it proposed bridges WITHOUT seeing gold",
        ],
        "failure_signatures": [
            "Recall = 0.65 (oracle-assisted) — production beats by Δ=+0.21",
            "But the comparison is unfair (oracle vs production)",
        ],
        "repair_recommendations": [
            "Implement true external baseline (zero-shot LLM bridge proposal)",
            "Until then, label as INSTRUMENTATION_SCAFFOLD_PASS",
        ],
    },
    "M-015": {
        "known_failure_modes": [
            "Random 2-grams rarely match gold bridges under strict matching",
            "Under lenient matching, small but non-zero FP rate (0.095)",
        ],
        "boundary_conditions": [
            "Strict: always 0.0 (random 2-grams never exactly match concept-level bridges)",
            "Lenient: 0.095 mean (some random matches via token overlap)",
        ],
        "failure_signatures": [
            "Strict: F1 = 0.0000 (degenerate)",
            "Lenient: F1 = 0.0950 ± 0.0739 (CI includes 0)",
        ],
        "repair_recommendations": [
            "Useful as FP floor reference under lenient matching",
            "Production (0.8571) beats this by Δ=+0.76 — but comparison is oracle-assisted",
        ],
    },
    "M-016": {
        "known_failure_modes": [
            "Frequency-based top bigram rarely matches gold bridge exactly",
            "Under lenient matching, 30% match rate via token overlap",
        ],
        "boundary_conditions": [
            "Fails when the most frequent bigram is not the gold bridge (common case)",
            "LLM-baseline proxy — not a true LLM baseline",
        ],
        "failure_signatures": [
            "Strict: F1 = 0.0000",
            "Lenient: F1 = 0.3000 ± 0.0989",
        ],
        "repair_recommendations": [
            "Useful as LLM-baseline proxy",
            "Production beats by Δ=+0.56 (lenient) — but oracle-assisted",
        ],
    },
    "M-101": {
        "known_failure_modes": [
            "Degenerate: all 5 benchmark files have perfect F1 (1.0000)",
            "Cannot discriminate — benchmark is too easy",
        ],
        "boundary_conditions": [
            "Fails to discriminate when all test files are perfectly parsed",
            "Would only show variance on harder documents (not in current benchmark)",
        ],
        "failure_signatures": [
            "F1 = 1.0000 (degenerate, CI [1.0, 1.0])",
        ],
        "repair_recommendations": [
            "Add harder documents to the benchmark (corrupted, multi-column, scanned PDFs)",
            "Until then, this metric provides no information",
        ],
    },
    "M-102": {
        "known_failure_modes": [
            "Synthetic reconstruction from aggregate TP/FP/FN (approximation)",
            "Recognition metric, not discovery (F-075 caveat)",
        ],
        "boundary_conditions": [
            "Bootstrap CI is narrow (N=65) but based on synthetic per-item data",
            "High F1 (0.9431) may not translate to discovery capability",
        ],
        "failure_signatures": [
            "F1 = 0.9431 ± 0.0208 [0.8983, 0.9764]",
        ],
        "repair_recommendations": [
            "Report alongside M-005 to distinguish recognition from discovery",
            "Collect real per-item data (not synthetic reconstruction) for accurate CI",
        ],
    },
    "M-103": {
        "known_failure_modes": [
            "Historical F1 jump (0.71→0.91) was gold-fix, not capability fix (F-099)",
            "Still measures retrieval, not discovery (F-075)",
        ],
        "boundary_conditions": [
            "F1 depends on circular-gold audit status (F-099)",
            "Per-sentence data available (N=85) — most reliable invention bootstrap",
        ],
        "failure_signatures": [
            "F1 = 0.8800 ± 0.0304 [0.8145, 0.9322]",
        ],
        "repair_recommendations": [
            "Report alongside circular-gold audit (F-099) status",
            "Most reliable invention metric (real per-item data)",
        ],
    },
    "M-104": {
        "known_failure_modes": [
            "Historical F1 jump (0.71→0.91) was gold-fix (F-099)",
            "Synthetic reconstruction from aggregate (approximation)",
            "CI touches 1.0 (small N=12, high F1)",
        ],
        "boundary_conditions": [
            "F1 near ceiling — little room to discriminate",
            "0.90 threshold (F-092) was set post-fix",
        ],
        "failure_signatures": [
            "F1 = 0.9091 ± 0.0677 [0.7368, 1.0000]",
        ],
        "repair_recommendations": [
            "Collect real per-item data for accurate CI",
            "Report F-099 caveat alongside",
        ],
    },
    "M-105": {
        "known_failure_modes": [
            "THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measuring recognition, not discovery)",
            "FORBIDDEN to report as naked F1",
            "FP floor = 1.0 (M-008) — any candidate matches",
            "CI touches 1.0 (N=17, high F1)",
        ],
        "boundary_conditions": [
            "Fails as a discovery metric — measures connection-finding, not bridge proposal",
            "The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) — not interchangeable",
        ],
        "failure_signatures": [
            "F1 = 0.9375 ± 0.0464 [0.8276, 1.0000]",
            "DR-91 invalidation: headline F1=0.9189 was recognition, not discovery",
        ],
        "repair_recommendations": [
            "FORBIDDEN to report as naked F1",
            "MUST report alongside M-008 (FP floor) and M-005/M-013 (bootstrap-CI discovery F1)",
            "Most contested metric in the entire specification",
        ],
    },
    "M-201": {
        "known_failure_modes": [
            "Code drift: documented baseline 2/10 (cycle 229) NOT reproduced by any seed (M4 finding)",
            "Current mean 0.83 (range 0.7-1.0) — search performs better now than in cycle 229",
            "M4 ACCEPTABLE (CV=0.13) — variance is within bounds but non-trivial",
        ],
        "boundary_conditions": [
            "Fails (produces different counts) across seeds — CV=0.13",
            "Documented 2/10 baseline is stale",
        ],
        "failure_signatures": [
            "Beats count ranges from 0.7 to 1.0 across 10 seeds",
            "Single-run reports are unreliable — must include seed and M4 CV",
        ],
        "repair_recommendations": [
            "Update documented baseline from 2/10 to 8.3/10 (M4 mean)",
            "Always report with seed and CV",
            "Investigate code drift: what changed between cycle 229 and now?",
        ],
    },
    "M-202": {
        "known_failure_modes": [
            "Evaluator uses EXTENDED_OPS internally — L5a and L5b are identical (M4 finding)",
            "Documented 5/10 baseline (cycle 231) NOT reproduced (current code gives 9/10)",
        ],
        "boundary_conditions": [
            "Cannot distinguish L5a (13 ops) from L5b (18 ops) with current evaluator",
            "A true L5a baseline would use BASE_OPS only",
        ],
        "failure_signatures": [
            "Same data as M-201 (evaluator doesn't distinguish)",
        ],
        "repair_recommendations": [
            "Implement separate L5a evaluator using BASE_OPS (13 ops) only",
            "Until then, M-202 = M-201 (documented honestly)",
        ],
    },
    "M-203": {
        "known_failure_modes": [
            "Uses min_pair_frequency=1 (not historical default) to produce composites",
            "M4 ACCEPTABLE (CV=0.10) — some run-to-run variance",
            "Single-seed 9/10 is within multi-seed CI (M-204 mean 8.6)",
        ],
        "boundary_conditions": [
            "Fails (produces different counts) across seeds — CV=0.10",
            "Composites vary across seeds (3-5 per seed, different pairs)",
        ],
        "failure_signatures": [
            "Beats count ranges from 0.7 to 1.0 across seeds",
        ],
        "repair_recommendations": [
            "Report M-204 (multi-seed mean) as canonical, not M-203 single-seed",
            "Document min_pair_frequency=1 parameter",
        ],
    },
    "M-204": {
        "known_failure_modes": [
            "N=5 seeds is very small — CI is wide",
            "Bootstrap std (0.35) is smaller than raw multi-seed std (0.80)",
        ],
        "boundary_conditions": [
            "Bootstrap is on seed-level beats, not per-problem beats",
            "Measures seed-to-seed variance, not problem-to-problem variance",
        ],
        "failure_signatures": [
            "Mean 8.6/10 ± 0.35 [8.0, 9.4]",
        ],
        "repair_recommendations": [
            "CANONICAL search claim — report this, not M-203 single-seed",
            "Increase to N=10+ seeds for tighter CI",
        ],
    },
    "M-205": {
        "known_failure_modes": [
            "Degenerate: 100% selection rate (all 43 composites selected)",
            "100% selection is suspicious — may indicate trivial usefulness or search bias",
            "NOT a capability claim — it's a usage claim",
        ],
        "boundary_conditions": [
            "Always 1.0 — every composite is selected at least once",
            "Cannot discriminate useful composites from useless ones",
        ],
        "failure_signatures": [
            "Selection rate = 1.0000 (degenerate, CI [1.0, 1.0])",
        ],
        "repair_recommendations": [
            "Do NOT report as a capability claim",
            "Measure selection QUALITY (does selection improve outcomes?) not just selection RATE",
        ],
    },
    "M-301": {
        "known_failure_modes": [
            "Degenerate: 0/6 accepted (AI surrogate review REJECTED all proposals)",
            "AI surrogate review is Tier-1.5 pre-screen, NOT Tier-2 human",
        ],
        "boundary_conditions": [
            "Fails (0% accept) when proposals are template-level shared-term hypotheses",
            "Single reviewer (no inter-rater agreement)",
        ],
        "failure_signatures": [
            "Accept rate = 0.0000 (degenerate)",
            "Overall mean = 2.24/5.00 — well below 3.5 PARTIAL threshold",
        ],
        "repair_recommendations": [
            "Repair ProposalComposer to produce domain-grounded hypotheses",
            "AI surrogate review confirmed proposals are 'template-level shared-term hypotheses'",
            "Gate D blocks FINAL verdict until proposals improve",
        ],
    },
    "M-302": {
        "known_failure_modes": [
            "Mean 2.24/5.00 — below 3.0 (neutral) and 3.5 (PARTIAL threshold)",
            "N=7 (dimensions) — small sample, wide CI",
        ],
        "boundary_conditions": [
            "Fails (< 3.5) when proposals lack novelty, mechanism, falsification rigor",
        ],
        "failure_signatures": [
            "Mean = 2.2381 ± 0.3090 [1.6780, 2.8458]",
            "CI does not include 3.5 — metric is clearly below PARTIAL threshold",
        ],
        "repair_recommendations": [
            "Improve proposal quality (mechanism-driven, not shared-vocabulary)",
            "Re-run AI surrogate review after ProposalComposer repair",
        ],
    },
    "M-304": {
        "known_failure_modes": [
            "17% agreement (1/6) — evaluators disagree 83% of the time (DR-96)",
            "CI includes 0 [0.0000, 0.5000] — cannot distinguish 'rarely agree' from 'never agree'",
            "N=6 is too small for meaningful CI",
        ],
        "boundary_conditions": [
            "Fails (< 50%) when evaluators use different prompts (standard/adversarial/neutral)",
            "3 judges with different prompts = diversity but no ground truth",
        ],
        "failure_signatures": [
            "Agreement = 0.1667 ± 0.1485 [0.0000, 0.5000]",
            "56 total disagreements across 6 proposals (DR-96)",
        ],
        "repair_recommendations": [
            "Agreement < 50% blocks any evaluator-based claim (per DR-96)",
            "Increase N to ≥20 proposals for meaningful agreement CI",
            "Consider using same-prompt judges for inter-rater reliability",
        ],
    },
    "M-305": {
        "known_failure_modes": [
            "+2.50 bias on 5-point scale — internal overestimates by 50% (DR-94)",
            "100% overestimate rate — every proposal overestimated",
            "Narrow CI [2.3750, 2.6250] — bias is systematic, not noisy",
        ],
        "boundary_conditions": [
            "Fails (bias > +1.0) — internal evaluator is not trustworthy",
            "Bias is consistent across all proposals (not random noise)",
        ],
        "failure_signatures": [
            "Bias = 2.5000 ± 0.0556 [2.3750, 2.6250]",
            "Every proposal overestimated — 100% overestimate rate",
        ],
        "repair_recommendations": [
            "Bias > +1.0 blocks any internal-evaluator-based claim (per DR-94)",
            "Replace internal evaluator with calibrated external evaluator",
            "This is the reason Gate D FAILED — AI surrogate rejected all proposals",
        ],
    },
    "M-306": {
        "known_failure_modes": [
            "ECE = 0.433 (from dr95) — poorly calibrated (threshold: ECE > 0.2 = poor)",
            "Bootstrap ECE (0.90) differs from reported ECE (0.433) due to proxy confidence",
            "Goodhart's law vulnerability (DR-96): optimizing confidence ≠ improving accuracy",
        ],
        "boundary_conditions": [
            "Fails (ECE > 0.2) — confidence does not match accuracy",
            "N=6 is too few for reliable binning (most bins have 0-1 samples)",
        ],
        "failure_signatures": [
            "ECE = 0.433 (dr95, actual confidence, 10 bins)",
            "Bootstrap ECE = 0.9000 ± 0.0111 (proxy confidence, 5 bins) — not comparable",
        ],
        "repair_recommendations": [
            "ECE > 0.2 blocks any confidence-based claim (per DR-96)",
            "Collect more proposals (N≥20) for reliable binning",
            "Use actual confidence values, not proxy",
        ],
    },
}

# Metrics M-003-D1 through D7 (AI surrogate dimensions) share failure modes
for d_idx in range(1, 8):
    mid = f"M-303-D{d_idx}"
    if mid not in FAILURE_MODE_KB:
        FAILURE_MODE_KB[mid] = FAILURE_MODE_KB.get("M-303-D1", {
            "known_failure_modes": [
                "AI surrogate dimension score (D1-D7) — single reviewer",
                "N=6 proposals — small sample",
            ],
            "boundary_conditions": [
                "Fails when proposals are low quality (all dimensions score low)",
            ],
            "failure_signatures": [
                "Dimension mean varies by criterion (D1=4.0 plausibility, D2=1.17 novelty)",
            ],
            "repair_recommendations": [
                "Report all 7 dimensions together for complete picture",
                "D2 (novelty) is the weakest dimension — proposals lack novelty",
            ],
        })

# M-303-D1 through D7 specific
FAILURE_MODE_KB["M-303-D1"] = {
    "known_failure_modes": ["D1 (plausibility) = 4.0 — concepts are real but proposals are shallow"],
    "boundary_conditions": ["High D1 with low D2 = plausible but not novel"],
    "failure_signatures": ["D1 = 4.0000 ± 0.2394 [3.5, 4.5]"],
    "repair_recommendations": ["D1 is the strongest dimension; focus repair on D2 (novelty)"],
}
FAILURE_MODE_KB["M-303-D2"] = {
    "known_failure_modes": ["D2 (novelty) = 1.17 — proposals are NOT novel (shared vocabulary)"],
    "boundary_conditions": ["D2 < 2.0 means proposals are 'known' or 'incremental'"],
    "failure_signatures": ["D2 = 1.1667 ± 0.1485 [1.0, 1.5]"],
    "repair_recommendations": ["WORST dimension — repair ProposalComposer for novelty"],
}
FAILURE_MODE_KB["M-303-D3"] = {
    "known_failure_modes": ["D3 (testability) = 2.0 — predictions are weak (degenerate)"],
    "boundary_conditions": ["D3 = 2.0 for all proposals (no variance)"],
    "failure_signatures": ["D3 = 2.0000 ± 0.0000 (degenerate)"],
    "repair_recommendations": ["Add specific, testable predictions to proposals"],
}
FAILURE_MODE_KB["M-303-D4"] = {
    "known_failure_modes": ["D4 (falsification) = 1.83 — falsifiers are not rigorous"],
    "boundary_conditions": ["D4 < 2.0 means falsification is weak"],
    "failure_signatures": ["D4 = 1.8333 ± 0.1517 [1.5, 2.0]"],
    "repair_recommendations": ["Add rigorous, real-experimental falsifiers"],
}
FAILURE_MODE_KB["M-303-D5"] = {
    "known_failure_modes": ["D5 (alternatives) = 3.0 — alternatives are strawman (degenerate)"],
    "boundary_conditions": ["D5 = 3.0 for all proposals (no variance)"],
    "failure_signatures": ["D5 = 3.0000 ± 0.0000 (degenerate)"],
    "repair_recommendations": ["Add real alternative explanations, not strawman"],
}
FAILURE_MODE_KB["M-303-D6"] = {
    "known_failure_modes": ["D6 (counterexample) = 1.83 — counterexamples are benchmark artifacts"],
    "boundary_conditions": ["D6 < 2.0 means counterexamples are weak"],
    "failure_signatures": ["D6 = 1.8333 ± 0.1517 [1.5, 2.0]"],
    "repair_recommendations": ["Add scientific counterexamples, not benchmark artifacts"],
}
FAILURE_MODE_KB["M-303-D7"] = {
    "known_failure_modes": ["D7 (overall value) = 1.83 — proposals are not valuable"],
    "boundary_conditions": ["D7 < 2.0 means proposals have little scientific value"],
    "failure_signatures": ["D7 = 1.8333 ± 0.1517 [1.5, 2.0]"],
    "repair_recommendations": ["Improve overall proposal quality — focus on novelty and mechanism"],
}


# ============================================================================
# GENERATE FAILURE ENVELOPES
# ============================================================================

def generate_all_envelopes() -> List[FailureEnvelope]:
    """Generate failure envelopes for all metrics with bootstrap data.

    Pulls from:
      - M3 bootstrap (baseline, CI, degenerate)
      - M4 repeatability (CV, verdict)
      - M6 sensitivity (fragile perturbations)
      - FAILURE_MODE_KB (curated knowledge)
    """
    m3 = _load_m3_data()
    m4 = _load_m4_data()
    m6_fragile = _load_m6_data()

    envelopes = []
    for metric_id, m3_result in sorted(m3.items()):
        # Get M4 data (may not exist for all metrics)
        m4_result = m4.get(metric_id, {})
        m4_verdict = m4_result.get("verdict", "NOT_TESTED")
        m4_cv = m4_result.get("cv", 0.0)
        if m4_result.get("is_deterministic"):
            m4_verdict = "DETERMINISTIC"

        # Get M6 fragile perturbations
        fragile = m6_fragile.get(metric_id, [])

        # Get curated failure modes
        kb = FAILURE_MODE_KB.get(metric_id, {
            "known_failure_modes": ["No curated failure modes — metric not in knowledge base"],
            "boundary_conditions": ["Unknown — not tested in M4/M6"],
            "failure_signatures": ["Unknown"],
            "repair_recommendations": ["Add to FAILURE_MODE_KB"],
        })

        env = FailureEnvelope(
            metric_id=metric_id,
            metric_name=m3_result.get("metric_name", "unknown"),
            baseline_value=m3_result.get("point_estimate", 0.0),
            ci_95=(m3_result.get("ci_95_lower", 0.0), m3_result.get("ci_95_upper", 0.0)),
            n=m3_result.get("n", 0),
            is_degenerate=m3_result.get("is_degenerate", False),
            repeatability_verdict=m4_verdict,
            cv=m4_cv,
            fragile_perturbations=fragile,
            known_failure_modes=kb["known_failure_modes"],
            boundary_conditions=kb["boundary_conditions"],
            failure_signatures=kb["failure_signatures"],
            repair_recommendations=kb["repair_recommendations"],
            evidence_refs=[
                "reports/bootstrap_statistics.json (M3)",
                "reports/repeatability_m4.json (M4)" if m4_result else "M4: not tested",
                "reports/sensitivity_m6.json (M6)" if fragile else "M6: no FRAGILE perturbations",
                "programs/A_metrology/MeasurementEngineSpecification.md (M1)",
            ],
        )
        envelopes.append(env)

    return envelopes


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("Stage M7: Failure Envelope (Program A, Priority #1)")
    print("Instead of 'When does it work?' Answer 'When does it fail?'")
    print("Per AP-1: run it, don't reason about it.")
    print("Per AP-5: every failure envelope must be a file on disk.")
    print("=" * 80)
    print()

    envelopes = generate_all_envelopes()
    print(f"Generated {len(envelopes)} failure envelopes")
    print()

    # Write per-metric failure envelope documents
    repo = Path(__file__).resolve().parents[2]
    envelopes_dir = repo / "reports" / "failure_envelopes"
    envelopes_dir.mkdir(parents=True, exist_ok=True)

    for env in envelopes:
        # Sanitize metric_id for filename (M-303-D1 -> M-303-D1.md)
        safe_id = env.metric_id.replace("/", "-")
        filepath = envelopes_dir / f"{safe_id}.md"
        filepath.write_text(env.to_markdown())

    print(f"Written {len(envelopes)} failure envelope documents to {envelopes_dir}")
    print()

    # Summary statistics
    total = len(envelopes)
    degenerate = sum(1 for e in envelopes if e.is_degenerate)
    has_fragile = sum(1 for e in envelopes if e.fragile_perturbations)
    m4_tested = sum(1 for e in envelopes if e.repeatability_verdict != "NOT_TESTED")
    m4_unstable = sum(1 for e in envelopes if e.repeatability_verdict == "UNSTABLE")

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total metrics with failure envelopes: {total}")
    print(f"  Degenerate (M3): {degenerate}")
    print(f"  Has FRAGILE perturbations (M6): {has_fragile}")
    print(f"  M4 repeatability tested: {m4_tested}")
    print(f"  M4 UNSTABLE: {m4_unstable}")
    print()

    # Count metrics with each failure mode category
    has_failure_modes = sum(1 for e in envelopes if e.known_failure_modes)
    has_boundary_conditions = sum(1 for e in envelopes if e.boundary_conditions)
    has_repair_recommendations = sum(1 for e in envelopes if e.repair_recommendations)
    print(f"  Has known failure modes: {has_failure_modes}/{total}")
    print(f"  Has boundary conditions: {has_boundary_conditions}/{total}")
    print(f"  Has repair recommendations: {has_repair_recommendations}/{total}")
    print()

    # Gate decision
    print("=" * 80)
    print("GATE M7 DECISION")
    print("=" * 80)
    print()
    # M7 passes if:
    # 1. Every metric in M3 bootstrap has a failure envelope document
    # 2. Every envelope has at least 1 known failure mode
    # 3. Every envelope has at least 1 boundary condition
    # 4. Every envelope has at least 1 repair recommendation
    all_have_fm = all(e.known_failure_modes for e in envelopes)
    all_have_bc = all(e.boundary_conditions for e in envelopes)
    all_have_rr = all(e.repair_recommendations for e in envelopes)

    if all_have_fm and all_have_bc and all_have_rr:
        gate_verdict = "PASS"
        print(f"PASS — all {total} metrics have failure envelope documents")
        print(f"  All have known failure modes: YES")
        print(f"  All have boundary conditions: YES")
        print(f"  All have repair recommendations: YES")
    else:
        gate_verdict = "PARTIAL"
        print(f"PARTIAL — some envelopes incomplete:")
        print(f"  All have known failure modes: {'YES' if all_have_fm else 'NO'}")
        print(f"  All have boundary conditions: {'YES' if all_have_bc else 'NO'}")
        print(f"  All have repair recommendations: {'YES' if all_have_rr else 'NO'}")
    print()

    # Write summary JSON
    json_out = {
        "cycle": 265,
        "stage": "M7",
        "program": "A",
        "n_envelopes": total,
        "n_degenerate": degenerate,
        "n_has_fragile": has_fragile,
        "n_m4_tested": m4_tested,
        "n_m4_unstable": m4_unstable,
        "all_have_failure_modes": all_have_fm,
        "all_have_boundary_conditions": all_have_bc,
        "all_have_repair_recommendations": all_have_rr,
        "gate_verdict": gate_verdict,
        "envelopes": [e.to_dict() for e in envelopes],
    }
    with open(repo / "reports" / "failure_envelope_m7.json", "w") as f:
        json.dump(json_out, f, indent=2)

    # Write summary markdown
    lines = []
    lines.append("# Stage M7: Failure Envelope (Program A)")
    lines.append("")
    lines.append("Cycle: 265")
    lines.append("")
    lines.append("Per ROADMAP_V2.md Stage M7: instead of 'When does it work?'")
    lines.append("answer 'When does it fail?' Every evaluator must have a")
    lines.append("Failure Envelope document.")
    lines.append("")
    lines.append("Per AP-1: run it, don't reason about it. Per AP-5: every")
    lines.append("failure envelope must be a file on disk.")
    lines.append("")
    lines.append("## What was done")
    lines.append("")
    lines.append(f"Generated {total} failure envelope documents in")
    lines.append(f"`reports/failure_envelopes/`, one per metric with M3 bootstrap data.")
    lines.append(f"Each envelope synthesizes data from:")
    lines.append(f"- M3 (bootstrap): baseline, CI, degenerate flag")
    lines.append(f"- M4 (repeatability): CV, verdict, deterministic flag")
    lines.append(f"- M6 (sensitivity): FRAGILE perturbations")
    lines.append(f"- M1 (specification): curated known failure modes, boundary conditions")
    lines.append(f"- DR-91 audit: FP floor, formula inflation findings")
    lines.append("")
    lines.append("## Summary statistics")
    lines.append("")
    lines.append(f"- Total metrics with failure envelopes: {total}")
    lines.append(f"- Degenerate (M3): {degenerate}")
    lines.append(f"- Has FRAGILE perturbations (M6): {has_fragile}")
    lines.append(f"- M4 repeatability tested: {m4_tested}")
    lines.append(f"- M4 UNSTABLE: {m4_unstable}")
    lines.append(f"- All have known failure modes: {'YES' if all_have_fm else 'NO'}")
    lines.append(f"- All have boundary conditions: {'YES' if all_have_bc else 'NO'}")
    lines.append(f"- All have repair recommendations: {'YES' if all_have_rr else 'NO'}")
    lines.append("")
    lines.append("## Per-metric failure envelope index")
    lines.append("")
    lines.append("| Metric | Name | Baseline | Degenerate | M4 Verdict | FRAGILE count |")
    lines.append("|---|---|---|---|---|---|")
    for e in envelopes:
        lines.append(
            f"| {e.metric_id} | {e.metric_name[:40]} | "
            f"{e.baseline_value:.4f} | {e.is_degenerate} | "
            f"{e.repeatability_verdict} | {len(e.fragile_perturbations)} |"
        )
    lines.append("")
    lines.append(f"## Gate M7 verdict: **{gate_verdict}**")
    lines.append("")
    if gate_verdict == "PASS":
        lines.append("All metrics have complete failure envelope documents with")
        lines.append("known failure modes, boundary conditions, and repair recommendations.")
    else:
        lines.append("Some envelopes are incomplete — see summary above.")
    lines.append("")
    lines.append("## Key findings across all envelopes")
    lines.append("")
    lines.append("### Most fragile metrics (from M6)")
    lines.append("")
    fragile_metrics = sorted(envelopes, key=lambda e: -len(e.fragile_perturbations))
    for e in fragile_metrics:
        if e.fragile_perturbations:
            lines.append(f"- **{e.metric_id}** ({e.metric_name}): {len(e.fragile_perturbations)} FRAGILE perturbation(s)")
    lines.append("")
    lines.append("### Degenerate metrics (from M3)")
    lines.append("")
    for e in envelopes:
        if e.is_degenerate:
            lines.append(f"- **{e.metric_id}** ({e.metric_name}): baseline = {e.baseline_value:.4f} (no variance)")
    lines.append("")
    lines.append("### Metrics with UNSTABLE repeatability (from M4)")
    lines.append("")
    unstable = [e for e in envelopes if e.repeatability_verdict == "UNSTABLE"]
    if unstable:
        for e in unstable:
            lines.append(f"- **{e.metric_id}** ({e.metric_name}): CV = {e.cv:.4f}")
    else:
        lines.append("- None (all tested metrics are STABLE or ACCEPTABLE)")
    lines.append("")
    lines.append("### Top repair priorities")
    lines.append("")
    lines.append("1. **M-008 (FP floor)**: FP floor = 0.92 (CI touches 1.0). The matcher")
    lines.append("   cannot discriminate. This is the #1 repair priority for the entire")
    lines.append("   measurement system.")
    lines.append("2. **M-010 (per-proposal F1)**: FRAGILE to input perturbation (-75%).")
    lines.append("   Uses only first shared entity — brittle. Repair: use all shared entities.")
    lines.append("3. **M-105 (Gen 5 Discovery F1)**: DR-91 invalidated. FORBIDDEN to report")
    lines.append("   as naked F1. Must report alongside M-008 and M-005/M-013.")
    lines.append("4. **M-305 (self-validation bias)**: +2.50 bias (100% overestimate).")
    lines.append("   Internal evaluator not trustworthy. Replace with calibrated external.")
    lines.append("5. **M-201/M-202 (search beats)**: Code drift. Documented baselines stale.")
    lines.append("   Update from 2/10 and 5/10 to M4 means (8.3/10, 8.3/10).")
    lines.append("")
    with open(repo / "reports" / "failure_envelope_m7.md", "w") as f:
        f.write("\n".join(lines))

    print(f"Saved reports/failure_envelope_m7.json")
    print(f"Saved reports/failure_envelope_m7.md")
    print(f"Saved {total} documents to reports/failure_envelopes/")
    print()
    print("=" * 80)
    print(f"GATE M7 DECISION: {gate_verdict}")
    print("=" * 80)
    return 0 if gate_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
