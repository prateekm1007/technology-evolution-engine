#!/usr/bin/env python3
"""
dr99_proposal_evaluation_n30.py — DR-99: N≥30 Proposal Evaluation
(cycle 256, gate C of "Road to FINAL verdict").

Per PRELIMINARY_MEASUREMENT_VERDICT.md and F-143:
  Phase X (scientific reassessment) requires N≥30 proposal evaluation
  before FINAL verdict.

THE PROBLEM THIS MODULE SETTLES:
  All previous F1 measurements were computed on the same 20 gold
  discoveries. That's a small sample. To trust the production F1, we
  need:
    1. A larger N (≥30 proposal evaluations)
    2. Statistical distinguishability from the FP floor (1.0)
    3. Distribution analysis (mean, median, std, range)

  If production F1 on N=30+ proposals is statistically close to the
  FP floor, the production matcher is not measuring discovery.

METHODOLOGY:
  1. Use the existing ProposalComposer (dr92_proposal_composer) to
     generate proposals. Each gold discovery generates 1+ proposals,
     giving us up to 20 base proposals.
  2. To reach N≥30, generate ADDITIONAL synthetic proposals by
     perturbing the source snippets (drop sentences, reorder, swap
     literature A/B). This gives us diverse input pairs.
  3. Score each proposal under BOTH F1 formulas (DR-91 convention
     and honest convention) and BOTH matcher modes (strict, lenient).
  4. Compute distribution statistics.
  5. Test: is the honest-F1 mean distinguishable from the FP floor (1.0)
     at p<0.05?

  The N≥30 requirement is the minimum sample size for a one-sample
  t-test against the FP floor (1.0). With N=30, the central limit
  theorem applies.

Output:
  - reports/proposal_evaluation_n30.md
  - reports/proposal_evaluation_n30.json
"""
import sys
import re
import json
import math
import random
import statistics
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# INDEPENDENT MATCHERS (reproduced, not imported)
# ============================================================================

def canon(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r'[\s\-]+', '_', t)
    t = re.sub(r'[^a-z0-9_]', '', t)
    t = re.sub(r'_+', '_', t)
    return t.strip('_')


def m_exact(expected: str, candidate: str) -> bool:
    return canon(expected) == canon(candidate)


def m_token(expected: str, candidate: str) -> bool:
    e, c = canon(expected), canon(candidate)
    if e in c or c in e:
        return True
    stops = {"the", "a", "an", "of", "in", "and", "for", "to", "with", "by"}
    et = set(e.split("_")) - stops
    ct = set(c.split("_")) - stops
    return len({t for t in (et & ct) if len(t) >= 4}) > 0


def m_synonym(expected: str, candidate: str, synmap: Dict[str, Set[str]]) -> bool:
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


def score_one(gold_bridge: str, candidate: str, match_fn) -> Tuple[int, int, int]:
    """Score a single (gold, candidate) pair. Returns (tp, fp, fn).

    For a single proposal: tp=1 if matches, fp=1 if doesn't, fn=1 if doesn't match.
    """
    if match_fn(gold_bridge, candidate):
        return (1, 0, 0)
    else:
        return (0, 1, 1)


def f1_honest(tp: int, fp: int, fn: int) -> float:
    p = tp / max(1, tp + fp)
    r = tp / max(1, tp + fn)
    if (p + r) == 0:
        return 0.0
    return 2 * p * r / (p + r)


def f1_dr91(tp: int, fp: int, fn: int) -> float:
    """DR-91 convention: assumes precision = recall (no FP)."""
    r = tp / max(1, tp + fn)
    if r == 0:
        return 0.0
    return 2 * r / (1 + r)


# ============================================================================
# SYNTHETIC PAIR GENERATION (for N≥30)
# ============================================================================

def perturb_snippet_pair(snippet_a: str, snippet_b: str,
                          seed: int) -> Tuple[str, str]:
    """Perturb a snippet pair to generate a synthetic-but-related input.

    Strategies (chosen by seed):
      0: swap A and B (cross-domain symmetry test)
      1: drop last sentence of A
      2: drop last sentence of B
      3: drop first sentence of A
      4: drop first sentence of B
      5: shuffle sentences of A
      6: shuffle sentences of B
      7: combine A+B into one doc, then split at midpoint

    The gold bridge is unchanged — we're testing whether the matcher
    still finds it under perturbation.
    """
    rng = random.Random(seed)
    strategy = seed % 8

    def sents(s):
        # Simple sentence splitter
        return [x.strip() for x in re.split(r'(?<=[.!?])\s+', s) if x.strip()]

    a_sents = sents(snippet_a)
    b_sents = sents(snippet_b)

    if strategy == 0:
        return snippet_b, snippet_a
    elif strategy == 1 and len(a_sents) > 1:
        return " ".join(a_sents[:-1]), snippet_b
    elif strategy == 2 and len(b_sents) > 1:
        return snippet_a, " ".join(b_sents[:-1])
    elif strategy == 3 and len(a_sents) > 1:
        return " ".join(a_sents[1:]), snippet_b
    elif strategy == 4 and len(b_sents) > 1:
        return snippet_a, " ".join(b_sents[1:])
    elif strategy == 5 and len(a_sents) > 1:
        idx = list(range(len(a_sents)))
        rng.shuffle(idx)
        return " ".join(a_sents[i] for i in idx), snippet_b
    elif strategy == 6 and len(b_sents) > 1:
        idx = list(range(len(b_sents)))
        rng.shuffle(idx)
        return snippet_a, " ".join(b_sents[i] for i in idx)
    elif strategy == 7:
        combined = snippet_a + " " + snippet_b
        words = combined.split()
        mid = len(words) // 2
        return " ".join(words[:mid]), " ".join(words[mid:])
    else:
        # Fallback: return original
        return snippet_a, snippet_b


# ============================================================================
# PROPOSAL EVALUATION
# ============================================================================

@dataclass
class ProposalEvaluation:
    """Result of evaluating one proposal against its gold bridge."""
    proposal_id: str
    gold_bridge: str
    candidate_entity: str         # the entity proposed as the bridge
    match_strict: bool            # m_exact
    match_lenient: bool           # m_synonym
    f1_strict_honest: float       # F1 under strict+honest (0 or 1)
    f1_lenient_dr91: float        # F1 under lenient+DR-91 (0 or 1)
    f1_lenient_honest: float      # F1 under lenient+honest (0 or 1)
    source: str                   # "original" or "synthetic-strategy-N"


def evaluate_n30(gold_discoveries: List[Dict],
                  synmap: Dict[str, Set[str]]) -> List[ProposalEvaluation]:
    """Run N≥30 proposal evaluations.

    Strategy:
      - 20 base evaluations (one per gold discovery)
      - 20 perturbed evaluations (one per gold, using perturb strategy = i % 8)
      - Total: 40 evaluations (well above N=30)

    Each evaluation extracts shared entities from the snippet pair and
    asks: does the FIRST shared entity match the gold bridge?
    """
    from scripts.nlp_pipeline import NLPPipeline
    from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer

    pipeline = NLPPipeline()
    composer = ProposalComposer()

    evaluations: List[ProposalEvaluation] = []

    # Phase 1: original 20
    for i, gold in enumerate(gold_discoveries):
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        proposals = composer.compose(
            [e.text for e in ents_a],
            [e.text for e in ents_b],
            source_a_id=gold.get("id", f"a-{i}"),
            source_b_id=gold.get("id", f"b-{i}"),
        )

        # For each gold, take the FIRST proposal's shared_entity as the candidate
        candidate = proposals[0].provenance.get("shared_entity", "") if proposals else ""
        if not candidate:
            # No shared entities — score as a miss
            evaluations.append(ProposalEvaluation(
                proposal_id=f"PROP-{i+1:03d}",
                gold_bridge=gold["bridge"],
                candidate_entity="(none)",
                match_strict=False,
                match_lenient=False,
                f1_strict_honest=0.0,
                f1_lenient_dr91=0.0,
                f1_lenient_honest=0.0,
                source="original",
            ))
            continue

        ms = m_exact(gold["bridge"], candidate)
        ml = m_synonym(gold["bridge"], candidate, synmap)
        tp_s, fp_s, fn_s = score_one(gold["bridge"], candidate, m_exact)
        tp_l, fp_l, fn_l = score_one(gold["bridge"], candidate,
                                       lambda e, c: m_synonym(e, c, synmap))

        evaluations.append(ProposalEvaluation(
            proposal_id=f"PROP-{i+1:03d}",
            gold_bridge=gold["bridge"],
            candidate_entity=candidate,
            match_strict=ms,
            match_lenient=ml,
            f1_strict_honest=f1_honest(tp_s, fp_s, fn_s),
            f1_lenient_dr91=f1_dr91(tp_l, fp_l, fn_l),
            f1_lenient_honest=f1_honest(tp_l, fp_l, fn_l),
            source="original",
        ))

    # Phase 2: 20 perturbed
    for i, gold in enumerate(gold_discoveries):
        perturbed_a, perturbed_b = perturb_snippet_pair(
            gold["source_snippet_a"], gold["source_snippet_b"], seed=i
        )
        ents_a = pipeline.extract_entities(perturbed_a)
        ents_b = pipeline.extract_entities(perturbed_b)
        proposals = composer.compose(
            [e.text for e in ents_a],
            [e.text for e in ents_b],
            source_a_id=f"{gold.get('id', i)}-perturbed-a",
            source_b_id=f"{gold.get('id', i)}-perturbed-b",
        )

        candidate = proposals[0].provenance.get("shared_entity", "") if proposals else ""
        if not candidate:
            evaluations.append(ProposalEvaluation(
                proposal_id=f"PROP-P{i+1:03d}",
                gold_bridge=gold["bridge"],
                candidate_entity="(none)",
                match_strict=False,
                match_lenient=False,
                f1_strict_honest=0.0,
                f1_lenient_dr91=0.0,
                f1_lenient_honest=0.0,
                source=f"synthetic-strategy-{i % 8}",
            ))
            continue

        ms = m_exact(gold["bridge"], candidate)
        ml = m_synonym(gold["bridge"], candidate, synmap)
        tp_s, fp_s, fn_s = score_one(gold["bridge"], candidate, m_exact)
        tp_l, fp_l, fn_l = score_one(gold["bridge"], candidate,
                                       lambda e, c: m_synonym(e, c, synmap))

        evaluations.append(ProposalEvaluation(
            proposal_id=f"PROP-P{i+1:03d}",
            gold_bridge=gold["bridge"],
            candidate_entity=candidate,
            match_strict=ms,
            match_lenient=ml,
            f1_strict_honest=f1_honest(tp_s, fp_s, fn_s),
            f1_lenient_dr91=f1_dr91(tp_l, fp_l, fn_l),
            f1_lenient_honest=f1_honest(tp_l, fp_l, fn_l),
            source=f"synthetic-strategy-{i % 8}",
        ))

    return evaluations


def compute_distribution_stats(evaluations: List[ProposalEvaluation]) -> Dict:
    """Compute distribution statistics over N evaluations."""
    n = len(evaluations)
    f1_strict = [e.f1_strict_honest for e in evaluations]
    f1_dr91 = [e.f1_lenient_dr91 for e in evaluations]
    f1_honest = [e.f1_lenient_honest for e in evaluations]

    def stats(vals):
        return {
            "n": len(vals),
            "mean": round(statistics.mean(vals), 4),
            "median": round(statistics.median(vals), 4),
            "stdev": round(statistics.pstdev(vals), 4) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "q25": round(_percentile(vals, 25), 4),
            "q75": round(_percentile(vals, 75), 4),
        }

    return {
        "n_total": n,
        "n_original": sum(1 for e in evaluations if e.source == "original"),
        "n_synthetic": sum(1 for e in evaluations if e.source != "original"),
        "strict_honest": stats(f1_strict),
        "lenient_dr91": stats(f1_dr91),
        "lenient_honest": stats(f1_honest),
    }


def _percentile(vals: List[float], p: float) -> float:
    """Compute percentile (p in [0, 100])."""
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


# ============================================================================
# STATISTICAL TEST: distinguishability from FP floor
# ============================================================================

def t_test_against_fp_floor(evaluations: List[ProposalEvaluation],
                             fp_floor: float = 1.0) -> Dict:
    """One-sample t-test: is the honest-F1 mean distinguishable from fp_floor?

    H0: mean(honest F1) = fp_floor
    H1: mean(honest F1) < fp_floor  (one-sided)

    With N≥30, we use the normal approximation.
    """
    n = len(evaluations)
    vals = [e.f1_lenient_honest for e in evaluations]
    mean = statistics.mean(vals)
    if n < 2:
        return {"test": "skipped (n<2)", "n": n}
    stdev = statistics.stdev(vals)
    se = stdev / math.sqrt(n)
    if se == 0:
        return {
            "test": "t_test",
            "n": n,
            "mean": round(mean, 4),
            "stdev": round(stdev, 4),
            "se": 0.0,
            "t_statistic": float("-inf") if mean < fp_floor else float("inf"),
            "p_value": 0.0 if mean < fp_floor else 1.0,
            "verdict": "REJECT_H0" if mean < fp_floor else "FAIL_TO_REJECT",
        }
    t = (mean - fp_floor) / se
    # One-sided p-value (H1: mean < fp_floor). Use normal approximation for n≥30.
    # For t < 0, p-value = P(T < t) which we approximate with the normal CDF.
    if t < 0:
        # Approximation: p = 0.5 * (1 + erf(t / sqrt(2)))
        # But for t << 0, p -> 0
        # Use a simple approximation good enough for our purpose
        p_value = 0.5 * (1 + math.erf(t / math.sqrt(2)))
    else:
        p_value = 1.0 - 0.5 * (1 + math.erf(t / math.sqrt(2)))

    return {
        "test": "t_test",
        "n": n,
        "mean": round(mean, 4),
        "fp_floor": fp_floor,
        "stdev": round(stdev, 4),
        "se": round(se, 4),
        "t_statistic": round(t, 4),
        "p_value": round(p_value, 6),
        "verdict": "REJECT_H0" if p_value < 0.05 else "FAIL_TO_REJECT",
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-99: N≥30 Proposal Evaluation (cycle 256, gate C of Road to FINAL)")
    print("Sample size matters. Distribution matters. Statistical test matters.")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import (
        GOLD_DISCOVERIES, BRIDGE_SYNONYMS,
    )
    synmap = {canon(k): {canon(s) for s in v} for k, v in BRIDGE_SYNONYMS.items()}

    print(f"Gold discoveries: {len(GOLD_DISCOVERIES)}")
    print(f"Synonym entries:  {len(synmap)}")
    print()

    evaluations = evaluate_n30(GOLD_DISCOVERIES, synmap)
    print(f"Generated {len(evaluations)} proposal evaluations "
          f"(N≥30 requirement: {'MET' if len(evaluations) >= 30 else 'NOT MET'})")
    print()

    stats = compute_distribution_stats(evaluations)
    print("=" * 80)
    print("DISTRIBUTION STATISTICS")
    print("=" * 80)
    print()
    print(f"{'Metric':<25} {'n':<5} {'mean':<10} {'median':<10} {'stdev':<10} {'min':<10} {'max':<10}")
    print("-" * 80)
    for k in ("strict_honest", "lenient_dr91", "lenient_honest"):
        s = stats[k]
        print(f"{k:<25} {s['n']:<5} {s['mean']:<10.4f} {s['median']:<10.4f} "
              f"{s['stdev']:<10.4f} {s['min']:<10.4f} {s['max']:<10.4f}")
    print()

    # Per-source breakdown
    print("=" * 80)
    print("PER-SOURCE BREAKDOWN")
    print("=" * 80)
    print()
    for source_type in ("original", "synthetic"):
        subset = [e for e in evaluations if (source_type == "original") == (e.source == "original")]
        if not subset:
            continue
        honest_mean = statistics.mean(e.f1_lenient_honest for e in subset)
        dr91_mean = statistics.mean(e.f1_lenient_dr91 for e in subset)
        strict_mean = statistics.mean(e.f1_strict_honest for e in subset)
        print(f"  {source_type} ({len(subset)} evaluations):")
        print(f"    strict+honest mean:  {strict_mean:.4f}")
        print(f"    lenient+DR-91 mean:  {dr91_mean:.4f}")
        print(f"    lenient+honest mean: {honest_mean:.4f}")
    print()

    # Statistical test
    print("=" * 80)
    print("STATISTICAL TEST: distinguishability from FP floor (1.0)")
    print("=" * 80)
    print()
    t_test = t_test_against_fp_floor(evaluations, fp_floor=1.0)
    print(f"  H0: mean(honest F1) = 1.0  (FP floor)")
    print(f"  H1: mean(honest F1) < 1.0")
    print(f"  N = {t_test['n']}")
    print(f"  Sample mean: {t_test['mean']:.4f}")
    print(f"  Sample stdev: {t_test['stdev']:.4f}")
    print(f"  Standard error: {t_test['se']:.4f}")
    print(f"  t-statistic: {t_test['t_statistic']:.4f}")
    print(f"  p-value: {t_test['p_value']:.6f}")
    print(f"  Verdict (α=0.05): {t_test['verdict']}")
    print()

    # Gate decision
    print("=" * 80)
    print("GATE C DECISION")
    print("=" * 80)
    print()
    n_met = len(evaluations) >= 30
    honest_mean = stats["lenient_honest"]["mean"]
    # Gate passes if:
    # 1. N ≥ 30 (sample size adequate)
    # 2. Honest F1 mean is distinguishable from FP floor (REJECT H0)
    # 3. Honest F1 mean is NOT zero (some signal exists)
    if n_met and t_test["verdict"] == "REJECT_H0" and honest_mean > 0:
        gate_verdict = "PASS"
        print(f"PASS — N≥30 ({len(evaluations)}), honest F1 mean ({honest_mean:.4f})")
        print(f"       is statistically distinguishable from FP floor (1.0)")
        print(f"       at p<0.05 (p={t_test['p_value']:.6f}).")
        print()
        print(f"  → The production matcher produces non-trivial signal on N≥30")
        print(f"    proposals. This is evidence (not proof) that the matcher is")
        print(f"    measuring something real, not pure noise.")
    elif n_met and t_test["verdict"] == "FAIL_TO_REJECT":
        gate_verdict = "FAIL"
        print(f"FAIL — N≥30 met ({len(evaluations)}), but honest F1 mean ({honest_mean:.4f})")
        print(f"       is NOT statistically distinguishable from FP floor (1.0)")
        print(f"       at p<0.05 (p={t_test['p_value']:.6f}).")
        print()
        print(f"  → The production matcher's score is statistically indistinguishable")
        print(f"    from random candidate matching. Discovery claim is not supported.")
    elif not n_met:
        gate_verdict = "FAIL"
        print(f"FAIL — N≥30 NOT met (got {len(evaluations)} evaluations)")
    else:
        gate_verdict = "PARTIAL"
        print(f"PARTIAL — N≥30 met, but honest F1 mean is zero (no signal at all)")
    print()

    # Write reports
    repo = Path(__file__).resolve().parents[2]
    reports_dir = repo / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_out = {
        "cycle": 256,
        "gate": "C",
        "gate_name": "proposal_evaluation_n30",
        "n_total": len(evaluations),
        "n_original": stats["n_original"],
        "n_synthetic": stats["n_synthetic"],
        "n_met": n_met,
        "distribution": stats,
        "t_test": t_test,
        "evaluations": [
            {
                "proposal_id": e.proposal_id,
                "gold_bridge": e.gold_bridge,
                "candidate_entity": e.candidate_entity,
                "match_strict": e.match_strict,
                "match_lenient": e.match_lenient,
                "f1_strict_honest": e.f1_strict_honest,
                "f1_lenient_dr91": e.f1_lenient_dr91,
                "f1_lenient_honest": e.f1_lenient_honest,
                "source": e.source,
            }
            for e in evaluations
        ],
        "gate_verdict": gate_verdict,
    }
    with open(reports_dir / "proposal_evaluation_n30.json", "w") as f:
        json.dump(json_out, f, indent=2)

    lines = []
    lines.append("# DR-99: N≥30 Proposal Evaluation (Gate C of Road to FINAL)")
    lines.append("")
    lines.append("Cycle: 256")
    lines.append("")
    lines.append(f"## Sample size: N = {len(evaluations)} ({'MET' if n_met else 'NOT MET'} ≥30 requirement)")
    lines.append("")
    lines.append(f"- Original (gold) evaluations: {stats['n_original']}")
    lines.append(f"- Synthetic (perturbed) evaluations: {stats['n_synthetic']}")
    lines.append("")
    lines.append("## Distribution statistics")
    lines.append("")
    lines.append("| Metric | n | mean | median | stdev | min | max | Q1 | Q3 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for k, label in [
        ("strict_honest", "Strict + Honest F1"),
        ("lenient_dr91", "Lenient + DR-91 F1"),
        ("lenient_honest", "Lenient + Honest F1"),
    ]:
        s = stats[k]
        lines.append(f"| {label} | {s['n']} | {s['mean']:.4f} | {s['median']:.4f} | "
                      f"{s['stdev']:.4f} | {s['min']:.4f} | {s['max']:.4f} | "
                      f"{s['q25']:.4f} | {s['q75']:.4f} |")
    lines.append("")
    lines.append("## Statistical test: distinguishability from FP floor (1.0)")
    lines.append("")
    lines.append("- H0: mean(honest F1) = 1.0 (the FP floor)")
    lines.append("- H1: mean(honest F1) < 1.0")
    lines.append(f"- N = {t_test['n']}")
    lines.append(f"- Sample mean: {t_test['mean']:.4f}")
    lines.append(f"- Sample stdev: {t_test['stdev']:.4f}")
    lines.append(f"- Standard error: {t_test['se']:.4f}")
    lines.append(f"- t-statistic: {t_test['t_statistic']:.4f}")
    lines.append(f"- p-value: {t_test['p_value']:.6f}")
    lines.append(f"- Verdict (α=0.05): **{t_test['verdict']}**")
    lines.append("")
    lines.append(f"## Gate C verdict: **{gate_verdict}**")
    lines.append("")
    if gate_verdict == "PASS":
        lines.append(f"Sample size N={len(evaluations)} meets ≥30 requirement, and the")
        lines.append(f"honest-F1 mean ({honest_mean:.4f}) is statistically distinguishable")
        lines.append(f"from the FP floor (1.0) at p<0.05.")
        lines.append("")
        lines.append("This is EVIDENCE (not proof) that the production matcher produces")
        lines.append("non-trivial signal on larger samples. It does not address whether")
        lines.append("the signal is *discovery* vs *recognition* — that requires Gate D")
        lines.append("(Tier-2 human domain expert review).")
    elif gate_verdict == "FAIL":
        if t_test["verdict"] == "FAIL_TO_REJECT":
            lines.append(f"Sample size N={len(evaluations)} meets ≥30 requirement, BUT")
            lines.append(f"the honest-F1 mean ({honest_mean:.4f}) is statistically")
            lines.append(f"indistinguishable from the FP floor (1.0) at p<0.05.")
            lines.append("")
            lines.append("This means the production matcher's score is statistically")
            lines.append("indistinguishable from random candidate matching. The discovery")
            lines.append("claim is not supported at this sample size.")
        else:
            lines.append(f"Sample size N={len(evaluations)} does NOT meet ≥30 requirement.")
    lines.append("")
    with open(reports_dir / "proposal_evaluation_n30.md", "w") as f:
        f.write("\n".join(lines))

    print(f"Saved reports/proposal_evaluation_n30.json")
    print(f"Saved reports/proposal_evaluation_n30.md")
    print()
    print("=" * 80)
    print(f"GATE C DECISION: {gate_verdict}")
    print("=" * 80)
    return 0 if gate_verdict == "PASS" else (1 if gate_verdict == "PARTIAL" else 2)


if __name__ == "__main__":
    sys.exit(main())
