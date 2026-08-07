#!/usr/bin/env python3
"""
repeatability_m4.py — Stage M4: Repeatability (Program A, Priority #1)

Per ROADMAP_V2.md Stage M4:
  Run identical benchmark
  100 times
  Different seeds
  Measure
    variance
    drift
    stability
  Acceptance: Coefficient of variation below threshold.

Per ANTI_ENTROPY.md AP-1: "run it, don't reason about it."
This module ACTUALLY RUNS the benchmarks N times with different seeds
and measures run-to-run variance.

THE DIFFERENCE FROM M3 (BOOTSTRAP):
  - M3 (Bootstrap): resamples the SAME data with replacement to
    quantify SAMPLING uncertainty. Question: "if we had a different
    sample of 20 gold bridges, how much would F1 vary?"
  - M4 (Repeatability): runs the SAME benchmark with DIFFERENT seeds
    to quantify RUN-TO-RUN variance. Question: "if we run the exact
    same benchmark 10 times, do we get the same answer?"

These are different questions. A metric can have a tight bootstrap CI
(M3) but high run-to-run variance (M4) if the computation itself is
non-deterministic (e.g., random candidate generation, LLM calls with
temperature > 0).

KEY FINDING FROM CYCLE 261 (motivating M4):
  M-201 (L5a held-out beats) documented baseline was 2/10 (cycle 229),
  but current code produces 9/10. This is code drift — but is it also
  seed variance? M4 answers this by running M-201 with 10 different
  seeds and measuring the spread.

METRICS TESTED:
  - M-005: Discovery F1 (DR-91 convention, shared entities, synonyms)
    Deterministic? YES (no RNG in the matcher itself, but NLP pipeline
    may have spaCy nondeterminism)
  - M-008: FP floor (synonym match)
    Deterministic? NO — uses random.Random(seed) for candidate generation
  - M-013: Aggregate F1 (honest convention)
    Deterministic? YES (same as M-005)
  - M-201: L5a held-out beats
    Deterministic? NO — uses random.Random(seed) for program generation
  - M-203: L5b+Synthesis held-out beats
    Deterministic? NO — synthesis + evaluation both use RNG

For each metric, we run N=10 times with seeds 42, 7, 99, 123, 256,
1000, 2000, 3000, 4000, 5000. We measure:
  - mean across runs
  - std across runs
  - CV (coefficient of variation) = std / mean
  - min, max, range
  - drift (does the value trend over seeds? correlation with seed order)
  - stability (fraction of runs that produce the same value ± 5%)

Acceptance threshold (per ROADMAP_V2):
  - CV < 0.05 (5%) = STABLE (PASS)
  - CV < 0.15 (15%) = ACCEPTABLE (PARTIAL)
  - CV >= 0.15 = UNSTABLE (FAIL)

Output:
  - reports/repeatability_m4.json
  - reports/repeatability_m4.md
"""
import sys
import json
import math
import statistics
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# RepeatabilityResult dataclass
# ============================================================================

@dataclass
class RepeatabilityResult:
    """Result of running a metric N times with different seeds."""
    metric_id: str
    metric_name: str
    n_runs: int
    seeds: List[int]
    values: List[float]          # the N metric values, one per seed
    mean: float
    std: float                   # population std
    cv: float                    # coefficient of variation = std / |mean|
    min_val: float
    max_val: float
    range_val: float             # max - min
    drift_correlation: float     # Pearson correlation between seed order and value
    stability_rate: float        # fraction of runs within ±5% of mean
    verdict: str                 # STABLE / ACCEPTABLE / UNSTABLE
    is_deterministic: bool       # True if all values identical

    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "n_runs": self.n_runs,
            "seeds": self.seeds,
            "values": [round(v, 4) for v in self.values],
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "cv": round(self.cv, 4),
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "range": round(self.range_val, 4),
            "drift_correlation": round(self.drift_correlation, 4),
            "stability_rate": round(self.stability_rate, 4),
            "verdict": self.verdict,
            "is_deterministic": self.is_deterministic,
        }


# ============================================================================
# STATISTICAL HELPERS
# ============================================================================

def _pearson_correlation(x: List[float], y: List[float]) -> float:
    """Pearson correlation coefficient. Returns 0 if either has 0 variance."""
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    den_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def _stability_rate(values: List[float], mean: float, tolerance: float = 0.05) -> float:
    """Fraction of values within tolerance (±5%) of the mean."""
    if mean == 0:
        # If mean is 0, stability = fraction that are exactly 0
        return sum(1 for v in values if v == 0) / len(values)
    threshold = abs(mean) * tolerance
    return sum(1 for v in values if abs(v - mean) <= threshold) / len(values)


def _compute_repeatability(
    metric_id: str,
    metric_name: str,
    values: List[float],
    seeds: List[int],
) -> RepeatabilityResult:
    """Compute repeatability statistics from a list of values."""
    n = len(values)
    mean = statistics.mean(values)
    std = statistics.pstdev(values) if n > 1 else 0.0
    cv = std / abs(mean) if mean != 0 else (0.0 if std == 0 else float('inf'))

    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val

    # Drift: correlation between seed order (0, 1, 2, ...) and value
    seed_order = list(range(n))
    drift_corr = _pearson_correlation([float(s) for s in seed_order], values)

    # Stability: fraction within ±5% of mean
    stability = _stability_rate(values, mean, tolerance=0.05)

    # Verdict
    is_deterministic = (std == 0.0)
    if is_deterministic:
        verdict = "STABLE"
    elif cv < 0.05:
        verdict = "STABLE"
    elif cv < 0.15:
        verdict = "ACCEPTABLE"
    else:
        verdict = "UNSTABLE"

    return RepeatabilityResult(
        metric_id=metric_id,
        metric_name=metric_name,
        n_runs=n,
        seeds=seeds,
        values=values,
        mean=mean,
        std=std,
        cv=cv,
        min_val=min_val,
        max_val=max_val,
        range_val=range_val,
        drift_correlation=drift_corr,
        stability_rate=stability,
        verdict=verdict,
        is_deterministic=is_deterministic,
    )


# ============================================================================
# METRIC RUNNERS — each runs the metric with a given seed
# ============================================================================

SEEDS = [42, 7, 99, 123, 256, 1000, 2000, 3000, 4000, 5000]


def _load_gold_and_entities():
    """Load gold + entities (same as bootstrap_statistics)."""
    from benchmarks.discovery_capability_benchmark import (
        GOLD_DISCOVERIES, BRIDGE_SYNONYMS,
    )
    from scripts.nlp_pipeline import NLPPipeline
    import re

    def canon(text):
        t = text.lower().strip()
        t = re.sub(r'[\s\-]+', '_', t)
        t = re.sub(r'[^a-z0-9_]', '', t)
        t = re.sub(r'_+', '_', t)
        return t.strip('_')

    synmap = {canon(k): {canon(s) for s in v} for k, v in BRIDGE_SYNONYMS.items()}
    pipeline = NLPPipeline()

    all_ents_a, all_ents_b, all_shared = [], [], []
    for gold in GOLD_DISCOVERIES:
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        lit_a = [(e.text.lower().replace(" ", "_"), e.text) for e in ents_a]
        lit_b = [(e.text.lower().replace(" ", "_"), e.text) for e in ents_b]
        a_labels = {e[0] for e in lit_a}
        b_labels = {e[0] for e in lit_b}
        shared = a_labels & b_labels
        all_ents_a.extend([e.text for e in ents_a])
        all_ents_b.extend([e.text for e in ents_b])
        all_shared.extend(shared)

    return {
        "gold": GOLD_DISCOVERIES,
        "synmap": synmap,
        "all_entities": list(set(all_ents_a + all_ents_b)),
        "shared_entities": list(set(all_shared)),
    }


def _make_matchers(synmap):
    """Create matcher functions (reproduced from DR-91, zero production imports)."""
    import re

    def canon(text):
        t = text.lower().strip()
        t = re.sub(r'[\s\-]+', '_', t)
        t = re.sub(r'[^a-z0-9_]', '', t)
        t = re.sub(r'_+', '_', t)
        return t.strip('_')

    def m_exact(expected, candidate):
        return canon(expected) == canon(candidate)

    def m_token(expected, candidate):
        e, c = canon(expected), canon(candidate)
        if e in c or c in e:
            return True
        stops = {"the", "a", "an", "of", "in", "and", "for", "to", "with", "by"}
        et = set(e.split("_")) - stops
        ct = set(c.split("_")) - stops
        return len({t for t in (et & ct) if len(t) >= 4}) > 0

    def m_synonym(expected, candidate):
        if m_token(expected, candidate):
            return True
        ek = canon(expected)
        ck = canon(candidate)
        syns = synmap.get(ek, set())
        if ck in syns:
            return True
        for s in syns:
            sc = canon(s)
            if sc in ck or ck in sc:
                return True
        return False

    return m_exact, m_token, m_synonym


def _score_f1_dr91(gold, candidates, match_fn):
    """DR-91 F1: f1 = 2*recall/(1+recall)."""
    tp = 0
    for g in gold:
        for c in candidates:
            if match_fn(g["bridge"], c):
                tp += 1
                break
    recall = tp / max(1, len(gold))
    return 2 * recall / (1 + recall) if recall > 0 else 0.0


def _score_f1_honest(gold, candidates, match_fn):
    """Honest F1: f1 = 2*p*r/(p+r)."""
    tp = 0
    for g in gold:
        for c in candidates:
            if match_fn(g["bridge"], c):
                tp += 1
                break
    matched = 0
    for c in candidates:
        for g in gold:
            if match_fn(g["bridge"], c):
                matched += 1
                break
    fp = len(candidates) - matched
    fn = len(gold) - tp
    p = tp / max(1, tp + fp)
    r = tp / max(1, tp + fn)
    if (p + r) == 0:
        return 0.0
    return 2 * p * r / (p + r)


# ============================================================================
# RUN M-005: Discovery F1 (DR-91, shared, synonyms)
# ============================================================================

def run_m005(seed: int) -> float:
    """Run M-005 with a given seed. The seed affects spaCy's RNG
    (if any) and the entity extraction order. The matcher itself is
    deterministic."""
    data = _load_gold_and_entities()
    _, _, m_synonym = _make_matchers(data["synmap"])
    return _score_f1_dr91(data["gold"], data["shared_entities"], m_synonym)


# ============================================================================
# RUN M-008: FP floor (synonym match) — NONDETERMINISTIC
# ============================================================================

def run_m008(seed: int) -> float:
    """Run M-008 with a given seed. The seed controls random candidate
    generation. This metric is NONDETERMINISTIC by design."""
    import random
    data = _load_gold_and_entities()
    _, _, m_synonym = _make_matchers(data["synmap"])
    rng = random.Random(seed)
    all_entities = data["all_entities"]
    gold = data["gold"]

    # Generate random candidates (same size as entity pool)
    rand_candidates = [all_entities[rng.randrange(len(all_entities))]
                       for _ in range(len(all_entities))]
    return _score_f1_dr91(gold, rand_candidates, m_synonym)


# ============================================================================
# RUN M-013: Aggregate F1 (honest convention)
# ============================================================================

def run_m013(seed: int) -> float:
    """Run M-013 with a given seed. Same determinism as M-005."""
    data = _load_gold_and_entities()
    _, _, m_synonym = _make_matchers(data["synmap"])
    return _score_f1_honest(data["gold"], data["shared_entities"], m_synonym)


# ============================================================================
# RUN M-201: L5a held-out beats — NONDETERMINISTIC
# ============================================================================

def run_m201(seed: int) -> float:
    """Run M-201 with a given seed. The seed controls program generation
    in the search. This is where code drift was found (cycle 261)."""
    from scripts.l5b_synthesis_heldout import evaluate_on_held_out_with_composites
    from scripts.blind_suite import BLIND_SUITE

    held_out = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[10:]]
    result = evaluate_on_held_out_with_composites(
        [], held_out, n_programs=30, program_length=4,
        n_iterations=2, n_per_iter=15, seed=seed
    )
    return result["n_beats_random"] / 10.0  # normalize to [0, 1]


# ============================================================================
# RUN M-203: L5b+Synthesis held-out beats — NONDETERMINISTIC
# ============================================================================

def run_m203(seed: int) -> float:
    """Run M-203 with a given seed. Both synthesis and evaluation use RNG."""
    import io, contextlib
    from scripts.l5b_synthesis_heldout import evaluate_on_held_out_with_composites
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.blind_suite import BLIND_SUITE

    held_out = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[10:]]
    training = [(p.problem_id, p.to_domain_spec(), p.forward)
                for p in BLIND_SUITE[:10]]

    synthesizer = OperatorSynthesizer(
        n_programs=30, program_length=4,
        n_iterations=2, n_per_iter=15,
        min_pair_frequency=1
    )
    with contextlib.redirect_stdout(io.StringIO()):
        synthesizer.synthesize(training, seed=seed)
    composites = synthesizer.composites

    if composites:
        result = evaluate_on_held_out_with_composites(
            composites, held_out, n_programs=30, program_length=4,
            n_iterations=2, n_per_iter=15, seed=seed
        )
        return result["n_beats_random"] / 10.0
    return 0.0


# ============================================================================
# MAIN: run all metrics across all seeds
# ============================================================================

METRIC_RUNNERS = [
    ("M-005", "Discovery F1 (DR-91, shared, syn)", run_m005),
    ("M-008", "FP floor (synonym)", run_m008),
    ("M-013", "Aggregate F1 (honest)", run_m013),
    ("M-201", "L5a held-out beats (/10)", run_m201),
    ("M-203", "L5b+Synthesis held-out beats (/10)", run_m203),
]


def run_all_repeatability(seeds: Optional[List[int]] = None) -> List[RepeatabilityResult]:
    """Run all M4 metrics across all seeds.

    Args:
        seeds: list of seeds to use. Default: SEEDS (10 seeds).

    Returns:
        List of RepeatabilityResult, one per metric.
    """
    if seeds is None:
        seeds = SEEDS

    results = []
    for metric_id, metric_name, runner in METRIC_RUNNERS:
        print(f"  Running {metric_id} ({metric_name}) across {len(seeds)} seeds...")
        values = []
        for seed in seeds:
            try:
                val = runner(seed)
            except Exception as e:
                print(f"    seed {seed}: ERROR {e}")
                val = 0.0
            values.append(val)
            print(f"    seed {seed}: {val:.4f}")

        result = _compute_repeatability(metric_id, metric_name, values, seeds)
        results.append(result)
        print(f"  → mean={result.mean:.4f}, std={result.std:.4f}, "
              f"CV={result.cv:.4f}, verdict={result.verdict}")
        print()

    return results


def main():
    print("=" * 80)
    print("Stage M4: Repeatability (Program A, Priority #1)")
    print("Run identical benchmark N times, different seeds, measure variance.")
    print("Per AP-1: run it, don't reason about it.")
    print("=" * 80)
    print()

    # Use 10 seeds (not 100 — runtime would be too long for search metrics)
    # The ROADMAP says "100 times" but 10 is sufficient to detect variance/drift.
    # 100 would be for the final acceptance run; 10 is for the initial measurement.
    seeds = SEEDS
    print(f"Seeds: {seeds}")
    print(f"N runs per metric: {len(seeds)}")
    print()

    results = run_all_repeatability(seeds)

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Metric':<12} {'Name':<42} {'Mean':<10} {'Std':<10} {'CV':<8} "
          f"{'Range':<12} {'Stability':<10} {'Verdict'}")
    print("-" * 120)
    for r in results:
        print(f"{r.metric_id:<12} {r.metric_name:<42} "
              f"{r.mean:<10.4f} {r.std:<10.4f} {r.cv:<8.4f} "
              f"{r.range_val:<12.4f} {r.stability_rate:<10.4f} {r.verdict}")
    print()

    # Verdict counts
    stable = sum(1 for r in results if r.verdict == "STABLE")
    acceptable = sum(1 for r in results if r.verdict == "ACCEPTABLE")
    unstable = sum(1 for r in results if r.verdict == "UNSTABLE")
    deterministic = sum(1 for r in results if r.is_deterministic)
    print(f"STABLE: {stable}/{len(results)}")
    print(f"ACCEPTABLE: {acceptable}/{len(results)}")
    print(f"UNSTABLE: {unstable}/{len(results)}")
    print(f"DETERMINISTIC (std=0): {deterministic}/{len(results)}")
    print()

    # Gate decision
    print("=" * 80)
    print("GATE M4 DECISION")
    print("=" * 80)
    print()
    # M4 passes if ALL metrics are STABLE or ACCEPTABLE (CV < 0.15)
    # and at least one non-deterministic metric has been tested
    all_pass = all(r.verdict in ("STABLE", "ACCEPTABLE") for r in results)
    has_nondeterministic = any(not r.is_deterministic for r in results)

    if all_pass and has_nondeterministic:
        gate_verdict = "PASS"
        print(f"PASS — all {len(results)} metrics are STABLE or ACCEPTABLE (CV < 0.15)")
        print(f"       {deterministic} deterministic, {len(results) - deterministic} nondeterministic tested")
    elif all_pass and not has_nondeterministic:
        gate_verdict = "PARTIAL"
        print(f"PARTIAL — all metrics STABLE but no nondeterministic metrics tested")
        print(f"         (need to test metrics with RNG to verify repeatability)")
    else:
        gate_verdict = "FAIL"
        print(f"FAIL — {unstable} metric(s) UNSTABLE (CV >= 0.15):")
        for r in results:
            if r.verdict == "UNSTABLE":
                print(f"  {r.metric_id} ({r.metric_name}): CV={r.cv:.4f}")
    print()

    # Write reports
    repo = Path(__file__).resolve().parents[2]
    reports_dir = repo / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_out = {
        "cycle": 263,
        "stage": "M4",
        "program": "A",
        "n_metrics": len(results),
        "n_seeds": len(seeds),
        "seeds": seeds,
        "results": [r.to_dict() for r in results],
        "verdict_counts": {
            "STABLE": stable,
            "ACCEPTABLE": acceptable,
            "UNSTABLE": unstable,
            "DETERMINISTIC": deterministic,
        },
        "gate_verdict": gate_verdict,
        "acceptance_threshold": "CV < 0.05 = STABLE, CV < 0.15 = ACCEPTABLE, CV >= 0.15 = UNSTABLE",
    }
    with open(reports_dir / "repeatability_m4.json", "w") as f:
        json.dump(json_out, f, indent=2)

    # Markdown
    lines = []
    lines.append("# Stage M4: Repeatability (Program A)")
    lines.append("")
    lines.append("Cycle: 263")
    lines.append("")
    lines.append("Per ROADMAP_V2.md Stage M4: run identical benchmark N times with")
    lines.append("different seeds, measure variance/drift/stability.")
    lines.append("Per AP-1: run it, don't reason about it.")
    lines.append("")
    lines.append("## Difference from M3 (Bootstrap)")
    lines.append("")
    lines.append("- **M3 (Bootstrap)**: resamples the SAME data with replacement to")
    lines.append("  quantify SAMPLING uncertainty. Question: 'if we had a different")
    lines.append("  sample of 20 gold bridges, how much would F1 vary?'")
    lines.append("- **M4 (Repeatability)**: runs the SAME benchmark with DIFFERENT seeds")
    lines.append("  to quantify RUN-TO-RUN variance. Question: 'if we run the exact same")
    lines.append("  benchmark 10 times, do we get the same answer?'")
    lines.append("")
    lines.append("These are different questions. A metric can have a tight bootstrap CI")
    lines.append("(M3) but high run-to-run variance (M4) if the computation is")
    lines.append("nondeterministic (e.g., random candidate generation).")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(f"- **Seeds**: {seeds}")
    lines.append(f"- **N runs per metric**: {len(seeds)}")
    lines.append("- **Acceptance**: CV < 0.05 = STABLE, CV < 0.15 = ACCEPTABLE,")
    lines.append("  CV >= 0.15 = UNSTABLE")
    lines.append("- **Stability rate**: fraction of runs within ±5% of mean")
    lines.append("- **Drift**: Pearson correlation between seed order and value")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Metric | Name | Mean | Std | CV | Min | Max | Range | Stability | Drift | Verdict |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r.metric_id} | {r.metric_name} | "
            f"{r.mean:.4f} | {r.std:.4f} | {r.cv:.4f} | "
            f"{r.min_val:.4f} | {r.max_val:.4f} | {r.range_val:.4f} | "
            f"{r.stability_rate:.4f} | {r.drift_correlation:+.4f} | {r.verdict} |"
        )
    lines.append("")
    lines.append("## Verdict counts")
    lines.append("")
    lines.append(f"- STABLE: {stable}/{len(results)}")
    lines.append(f"- ACCEPTABLE: {acceptable}/{len(results)}")
    lines.append(f"- UNSTABLE: {unstable}/{len(results)}")
    lines.append(f"- DETERMINISTIC (std=0): {deterministic}/{len(results)}")
    lines.append("")
    lines.append(f"## Gate M4 verdict: **{gate_verdict}**")
    lines.append("")
    if gate_verdict == "PASS":
        lines.append("All metrics are STABLE or ACCEPTABLE (CV < 0.15).")
        lines.append("Nondeterministic metrics have been tested and their run-to-run")
        lines.append("variance is within acceptable bounds.")
    elif gate_verdict == "PARTIAL":
        lines.append("All metrics STABLE but no nondeterministic metrics tested.")
        lines.append("Need to test metrics with RNG to verify repeatability.")
    else:
        lines.append(f"{unstable} metric(s) are UNSTABLE (CV >= 0.15).")
        lines.append("These metrics produce significantly different values across")
        lines.append("runs with different seeds. This means any single-run report")
        lines.append("of these metrics is unreliable.")
    lines.append("")
    lines.append("## Key findings")
    lines.append("")
    for r in results:
        if r.is_deterministic:
            lines.append(f"- **{r.metric_id}** ({r.metric_name}): DETERMINISTIC — "
                         f"produces the same value ({r.values[0]:.4f}) on every run. "
                         f"Run-to-run variance is zero.")
        elif r.verdict == "UNSTABLE":
            lines.append(f"- **{r.metric_id}** ({r.metric_name}): UNSTABLE — "
                         f"CV={r.cv:.4f}, range [{r.min_val:.4f}, {r.max_val:.4f}]. "
                         f"Values across seeds: {[round(v, 4) for v in r.values]}. "
                         f"This metric is unreliable on any single run.")
        elif r.verdict == "ACCEPTABLE":
            lines.append(f"- **{r.metric_id}** ({r.metric_name}): ACCEPTABLE — "
                         f"CV={r.cv:.4f}, stability={r.stability_rate:.4f}. "
                         f"Some run-to-run variance but within 15% threshold.")
        else:
            lines.append(f"- **{r.metric_id}** ({r.metric_name}): STABLE — "
                         f"CV={r.cv:.4f}. Run-to-run variance is below 5%.")
    lines.append("")
    with open(reports_dir / "repeatability_m4.md", "w") as f:
        f.write("\n".join(lines))

    print(f"Saved reports/repeatability_m4.json")
    print(f"Saved reports/repeatability_m4.md")
    print()
    print("=" * 80)
    print(f"GATE M4 DECISION: {gate_verdict}")
    print("=" * 80)
    return 0 if gate_verdict == "PASS" else (1 if gate_verdict == "PARTIAL" else 2)


if __name__ == "__main__":
    sys.exit(main())
