#!/usr/bin/env python3
"""
l5b_parameterized.py — L5b.2: Parameterized composites (cycle 238).

Per auditor's update #28:
  "Build L5b.2: scripts/l5b_parameterized.py with
   ParameterizedCompositeOperator (alpha param) +
   learn_alpha_from_landscape().

   Instead of narrow_iqr (fixed), learn narrow_iqr(alpha) where
   alpha = f(landscape). For example:
     alpha = 0.2 + 0.5*bimodality - 0.3*noise + 0.1*interaction
   Now the operator itself becomes adaptive. That is a qualitatively
   new primitive."

HONEST NAMING (per anti-entropy #5):
  This is L5b.2: PARAMETERIZED composites. NOT "operator discovery."
  The parameterized operators are still composed from existing
  primitives — but they have a LEARNED PARAMETER (alpha) that makes
  them adaptive. This is qualitatively different from fixed composites
  (L5b.1) because:
    narrow_iqr(0.4) ≠ narrow_iqr(0.8)
  Those are genuinely different operators with different behavior.

  The honest claim: "Parameterized composites with landscape-adaptive
  alpha. The operator's behavior changes based on landscape statistics.
  This is a new primitive type (parameterized), not just a longer
  sequence."

  NOT: "operator discovery" (the underlying ops are still existing ones).
  NOT: "AlphaDev" (no genuinely new algorithmic structure).

WHAT THIS MODULE DOES:
  1. ParameterizedCompositeOperator: a composite with a parameter alpha
     that controls the narrowing strength.
  2. learn_alpha_from_landscape(): computes alpha from landscape stats
     (bimodality, skew, interaction, nonzero_fraction).
  3. The executor applies alpha to the NARROW operations, making them
     adaptive: high alpha = aggressive narrowing, low alpha = gentle.
  4. Run entropy_benchmark.py to check if parameterized composites
     BREAK the saturation detected in cycle 237.

THE SCIENTIFIC QUESTION:
  Does adding a learned parameter (alpha) to composites break the
  saturation ceiling? If yes, parameterized operators capture
  information that fixed composites cannot. If no, the saturation
  is fundamental to the current DSL, not just to composition depth.

  The cycle 237 entropy benchmark showed: pairs → triples = 7.1×
  complexity, +0 performance (saturation). If parameterized composites
  show performance increasing WITH complexity (no saturation), that's
  evidence the parameter captures real information.
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Any
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.l5_search_discovery import (
    OpType, OptimizerProgram, ProgramExecutor, ALL_OPS,
)
from scripts.l5b_operator_discovery import (
    CombinatorialOpType, ExtendedProgramExecutor, EXTENDED_OPS,
)
from scripts.l5b_synthesis import CompositeOperator, OperatorSynthesizer
from scripts.meta_invention import LandscapeClassifier, LandscapeSignature


# ============================================================================
# PARAMETERIZED COMPOSITE OPERATOR
# ============================================================================

@dataclass
class ParameterizedCompositeOperator:
    """A composite operator with a LEARNED PARAMETER alpha.

    HONEST LABEL (cycle 238): This is a PARAMETERIZED composite, NOT
    a "discovered" operator. The underlying operations are existing
    DSL primitives. The innovation is the PARAMETER: alpha controls
    the narrowing strength, and alpha is LEARNED FROM LANDSCAPE STATS.

    This is qualitatively different from fixed composites (L5b.1):
      narrow_iqr(0.4) ≠ narrow_iqr(0.8)
    Different alpha values produce genuinely different operator behavior.
    The operator ADAPTS to the landscape — that's a new primitive type.

    The parameter alpha is computed by learn_alpha_from_landscape():
      alpha = f(bimodality, skew_ratio, interaction_index, nonzero_fraction)

    Example:
      ParameterizedCompositeOperator(
          "PARAM-001", "adaptive_narrow_mutate",
          [NARROW_IQR, MUTATE],
          alpha_formula="0.3 + 0.4*bimodality - 0.2*skew_ratio"
      )
      → on a bimodal landscape (bimodality=0.8): alpha = 0.3+0.32-0.04 = 0.58
      → on a smooth landscape (bimodality=0.1): alpha = 0.3+0.04-0.04 = 0.30
      → the narrowing is MORE aggressive on bimodal landscapes
    """
    composite_id: str          # e.g., "PARAM-001"
    name: str                  # human-readable name
    constituents: List[Any]    # list of OpType or CombinatorialOpType
    alpha: float = 0.5         # the learned parameter (0=gentle, 1=aggressive)
    alpha_formula: str = ""    # human-readable formula for alpha
    selection_count: int = 0
    fitness_when_selected: float = 0.0

    def to_composite_operator(self) -> CompositeOperator:
        """Convert to CompositeOperator for compatibility."""
        return CompositeOperator(
            composite_id=self.composite_id,
            name=f"{self.name}(alpha={self.alpha:.3f})",
            constituents=self.constituents,
            selection_count=self.selection_count,
            fitness_when_selected=self.fitness_when_selected,
        )

    def to_dict(self) -> Dict:
        return {
            "composite_id": self.composite_id,
            "name": self.name,
            "constituents": [str(op) for op in self.constituents],
            "alpha": round(self.alpha, 4),
            "alpha_formula": self.alpha_formula,
            "selection_count": self.selection_count,
            "fitness_when_selected": round(self.fitness_when_selected, 4),
            "type": "parameterized",  # NOT "discovered"
        }


# ============================================================================
# LEARN ALPHA FROM LANDSCAPE
# ============================================================================

def learn_alpha_from_landscape(sig: LandscapeSignature) -> Tuple[float, str]:
    """Compute alpha from landscape statistics.

    The formula (hand-designed, NOT discovered):
      alpha = 0.2 + 0.5*bimodality - 0.3*skew_ratio + 0.1*interaction_index

    Interpretation:
    - High bimodality → more aggressive narrowing (the landscape has
      two peaks; narrow aggressively to commit to one)
    - High skew_ratio → less aggressive (the landscape is smooth;
      gentle narrowing preserves diversity)
    - High interaction → slightly more aggressive (variables interact;
      narrowing one affects others)

    Returns (alpha, formula_string).
    Alpha is clamped to [0.1, 0.9].
    """
    bimod = sig.bimodality
    skew = min(1.0, sig.skew_ratio)
    inter = sig.interaction_index

    alpha = 0.2 + 0.5 * bimod - 0.3 * skew + 0.1 * inter
    alpha = max(0.1, min(0.9, alpha))

    formula = f"0.2 + 0.5*{bimod:.3f} - 0.3*{skew:.3f} + 0.1*{inter:.3f} = {alpha:.3f}"
    return alpha, formula


# ============================================================================
# PARAMETERIZED PROGRAM EXECUTOR
# ============================================================================

class ParameterizedProgramExecutor(ExtendedProgramExecutor):
    """ExtendedProgramExecutor that applies alpha to NARROW operations.

    When executing NARROW_IQR or NARROW_TIGHT, the narrowing strength
    is multiplied by alpha. This makes the composite's behavior
    ADAPTIVE — it narrows more aggressively when alpha is high.

    This is the key innovation: the SAME composite operator produces
    DIFFERENT behavior on different landscapes, because alpha is
    computed from landscape statistics.
    """

    def __init__(self, domain_spec: Dict, alpha: float = 0.5):
        super().__init__(domain_spec)
        self.alpha = alpha  # the learned parameter

    def _execute_op(self, op, candidates: List, rng: random.Random) -> List:
        """Execute op, applying alpha to narrowing operations."""
        # Check if it's a narrowing op that should be parameterized
        if op == OpType.NARROW_IQR:
            return self._op_narrow_iqr_parameterized(candidates, rng)
        elif op == OpType.NARROW_TIGHT:
            return self._op_narrow_tight_parameterized(candidates, rng)
        else:
            return super()._execute_op(op, candidates, rng)

    def _op_narrow_iqr_parameterized(self, candidates: List, rng: random.Random) -> List:
        """NARROW_IQR with alpha-controlled narrowing strength.

        alpha=0.5 (default) → standard narrowing (15% step, same as parent)
        alpha=0.9 (aggressive) → faster narrowing (25% step)
        alpha=0.1 (gentle) → slower narrowing (5% step)
        """
        if not candidates:
            return candidates
        sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
        top = sorted_c[:max(2, len(sorted_c) // 4)]

        # Alpha controls the narrowing step size
        # Standard: 15% step. Alpha scales this: step = 0.15 * (0.5 + alpha)
        step = 0.15 * (0.5 + self.alpha)

        for v in self.domain["design_vars"]:
            name = v["name"]
            vals = sorted(c.design_point[name] for c in top)
            n = len(vals)
            win_lo = vals[n // 4]
            win_hi = vals[3 * n // 4]
            lo, hi = self.original_bounds[name]
            cur_lo, cur_hi = self.policy[name]
            new_lo = (1 - step) * cur_lo + step * win_lo
            new_hi = (1 - step) * cur_hi + step * win_hi
            min_span = 0.30 * (hi - lo)
            if new_hi - new_lo < min_span:
                center = (new_lo + new_hi) / 2
                new_lo = max(lo, center - min_span / 2)
                new_hi = min(hi, center + min_span / 2)
            if new_hi > new_lo:
                self.policy[name] = (new_lo, new_hi)
        return candidates

    def _op_narrow_tight_parameterized(self, candidates: List, rng: random.Random) -> List:
        """NARROW_TIGHT with alpha-controlled padding."""
        if not candidates:
            return candidates
        sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
        top = sorted_c[:max(1, len(sorted_c) // 10)]

        # Alpha controls padding: high alpha = less padding (more aggressive)
        pad_fraction = 0.05 * (1.5 - self.alpha)  # alpha=0.5 → 0.05; alpha=0.9 → 0.03

        for v in self.domain["design_vars"]:
            name = v["name"]
            vals = [c.design_point[name] for c in top]
            win_lo, win_hi = min(vals), max(vals)
            lo, hi = self.original_bounds[name]
            pad = pad_fraction * (hi - lo)
            new_lo = max(lo, win_lo - pad)
            new_hi = min(hi, win_hi + pad)
            if new_hi > new_lo:
                self.policy[name] = (new_lo, new_hi)
        return candidates


# ============================================================================
# PARAMETERIZED SYNTHESIS LOOP
# ============================================================================

class ParameterizedSynthesizer:
    """L5b.2: Synthesize parameterized composites with landscape-adaptive alpha.

    The loop:
    1. Run program discovery on base DSL (same as L5b.1)
    2. Find frequent pairs (same as L5b.1)
    3. For each pair, create a ParameterizedCompositeOperator
    4. For each TRAINING landscape, compute alpha via learn_alpha_from_landscape()
    5. Evaluate the parameterized composite with the computed alpha
    6. Test on HELD-OUT landscapes: compute alpha per landscape, evaluate

    The key difference from L5b.1: the composite's behavior CHANGES
    based on the landscape. This is adaptive, not fixed.
    """

    def __init__(self, n_programs: int = 30, program_length: int = 4,
                 n_iterations: int = 2, n_per_iter: int = 15,
                 min_pair_frequency: int = 1):
        self.n_programs = n_programs
        self.program_length = program_length
        self.n_iterations = n_iterations
        self.n_per_iter = n_per_iter
        self.min_pair_frequency = min_pair_frequency
        self.parameterized_composites: List[ParameterizedCompositeOperator] = []

    def _run_program_discovery(self, training_domains, seed=42):
        """Run random program discovery on base DSL."""
        rng = random.Random(seed)
        results = []
        for i in range(self.n_programs):
            ops = [rng.choice(EXTENDED_OPS) for _ in range(self.program_length)]
            prog = OptimizerProgram(program_id=f"PARAM-DISC-{i+1:03d}", operations=ops)
            improvements = []
            for name, spec, fn in training_domains:
                executor = ExtendedProgramExecutor(spec)
                try:
                    iters = executor.execute_program(prog, fn,
                                                      n_iterations=self.n_iterations,
                                                      n_per_iter=self.n_per_iter, seed=42)
                    improvements.append(iters[-1]["best_outcome"] - iters[0]["best_outcome"])
                except:
                    improvements.append(-1e6)
            prog.fitness = sum(improvements) / len(improvements) if improvements else -1e6
            results.append((prog, prog.fitness))
        return results

    def synthesize(self, training_domains, seed=42):
        """Synthesize parameterized composites from frequent pairs."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()

        # Phase 1: Run program discovery
        with redirect_stdout(f):
            results = self._run_program_discovery(training_domains, seed)

        # Phase 2: Find frequent pairs
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        top_half = sorted_results[:max(5, len(sorted_results) // 2)]

        pair_freq = defaultdict(int)
        pair_fitness = defaultdict(list)
        for prog, fit in top_half:
            for i in range(len(prog.operations) - 1):
                pair = (prog.operations[i], prog.operations[i + 1])
                pair_freq[pair] += 1
                pair_fitness[pair].append(fit)

        # Phase 3: Create parameterized composites
        for pair, count in pair_freq.items():
            if count >= self.min_pair_frequency:
                op1, op2 = pair
                avg_fit = sum(pair_fitness[pair]) / len(pair_fitness[pair])
                name = f"param_{op1.value[:8]}_{op2.value[:8]}"

                # Compute alpha from AVERAGE landscape stats across training
                alphas = []
                for _, spec, fn in training_domains:
                    rng2 = random.Random(42)
                    cands = []
                    for _ in range(50):
                        dp = {}
                        for v in spec["design_vars"]:
                            lo, hi = v["bounds"]
                            if lo > 0 and hi / lo > 100:
                                dp[v["name"]] = math.exp(rng2.uniform(math.log(lo), math.log(hi)))
                            else:
                                dp[v["name"]] = rng2.uniform(lo, hi)
                        o, _ = fn(dp)
                        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
                        cands.append(c)
                    sig = LandscapeClassifier().classify(cands, spec["design_vars"])
                    alpha, formula = learn_alpha_from_landscape(sig)
                    alphas.append(alpha)

                avg_alpha = sum(alphas) / len(alphas) if alphas else 0.5
                avg_alpha = max(0.1, min(0.9, avg_alpha))

                pcomp = ParameterizedCompositeOperator(
                    composite_id=f"PARAM-{len(self.parameterized_composites) + 1:03d}",
                    name=name,
                    constituents=[op1, op2],
                    alpha=avg_alpha,
                    alpha_formula=f"avg of {len(alphas)} landscapes = {avg_alpha:.3f}",
                    fitness_when_selected=avg_fit,
                )
                self.parameterized_composites.append(pcomp)

        return self.parameterized_composites


# ============================================================================
# HELD-OUT EVALUATION WITH PARAMETERIZED COMPOSITES
# ============================================================================

def evaluate_parameterized_on_held_out(parameterized_composites, held_out_domains,
                                        n_programs=20, program_length=4,
                                        n_iterations=2, n_per_iter=12, seed=42):
    """Evaluate parameterized DSL on held-out.

    For each held-out problem:
    1. Compute alpha from the held-out landscape
    2. Create a ParameterizedProgramExecutor with that alpha
    3. Run programs using parameterized composites + base ops
    """
    rng = random.Random(seed)
    results = []

    for name, spec, fn in held_out_domains:
        # Compute alpha from this held-out landscape
        cands = []
        for _ in range(50):
            dp = {}
            for v in spec["design_vars"]:
                lo, hi = v["bounds"]
                if lo > 0 and hi / lo > 100:
                    dp[v["name"]] = math.exp(rng.uniform(math.log(lo), math.log(hi)))
                else:
                    dp[v["name"]] = rng.uniform(lo, hi)
            o, _ = fn(dp)
            c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
            cands.append(c)
        sig = LandscapeClassifier().classify(cands, spec["design_vars"])
        alpha, formula = learn_alpha_from_landscape(sig)

        # Build operator set: base + parameterized composites (as tokens)
        composite_tokens = [f"PARAM:{c.name}" for c in parameterized_composites]
        extended = list(EXTENDED_OPS) + composite_tokens

        best_outcome = -math.inf
        for _ in range(n_programs):
            ops_seq = []
            for _ in range(program_length):
                token = rng.choice(extended)
                if isinstance(token, str) and token.startswith("PARAM:"):
                    comp_name = token.split(":", 1)[1]
                    comp = next(c for c in parameterized_composites if c.name == comp_name)
                    ops_seq.extend(comp.constituents)
                    comp.selection_count += 1
                else:
                    ops_seq.append(token)

            prog = OptimizerProgram(program_id=f"PARAM-HELD-{name}", operations=ops_seq)
            executor = ParameterizedProgramExecutor(spec, alpha=alpha)
            try:
                iters = executor.execute_program(prog, fn,
                                                  n_iterations=n_iterations,
                                                  n_per_iter=n_per_iter, seed=seed)
                outcome = iters[-1]["best_outcome"]
            except:
                outcome = -1e6
            best_outcome = max(best_outcome, outcome)

        # Random baseline
        from scripts.comparative_benchmark import run_optimizer, RandomRestartOptimizer
        rand_opt = RandomRestartOptimizer(spec)
        rand_iters = run_optimizer(spec, fn, rand_opt,
                                    n_iterations=n_iterations, n_per_iter=n_per_iter, seed=seed)
        rand_best = rand_iters[-1]["best_outcome"]

        beats = best_outcome > rand_best + 1e-9
        results.append({
            "domain": name,
            "alpha": round(alpha, 3),
            "alpha_formula": formula,
            "param_best": best_outcome,
            "random_best": rand_best,
            "beats_random": beats,
        })

    n_beats = sum(1 for r in results if r["beats_random"])
    return {
        "results": results,
        "n_beats_random": n_beats,
        "n_total": len(results),
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 90)
    print("L5b.2 PARAMETERIZED COMPOSITES (cycle 238)")
    print("narrow_iqr(alpha) where alpha = f(landscape)")
    print("HONEST LABEL: parameterized, NOT discovered")
    print("=" * 90)
    print()

    from scripts.blind_suite import BLIND_SUITE

    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    # Phase 1: Synthesize parameterized composites
    print("=" * 90)
    print("PHASE 1: Synthesize parameterized composites on training")
    print("=" * 90)
    print()

    syn = ParameterizedSynthesizer(
        n_programs=30, program_length=4,
        n_iterations=2, n_per_iter=12,
        min_pair_frequency=1,
    )
    pcomps = syn.synthesize(training, seed=42)

    print(f"Parameterized composites synthesized: {len(pcomps)}")
    for pc in pcomps[:10]:
        print(f"  {pc.composite_id}: {pc.name} alpha={pc.alpha:.3f} "
              f"({pc.alpha_formula})")
    print()

    if not pcomps:
        print("No parameterized composites synthesized.")
        return

    # Phase 2: Evaluate on held-out
    print("=" * 90)
    print("PHASE 2: Evaluate parameterized DSL on held-out")
    print("=" * 90)
    print()

    for pc in pcomps:
        pc.selection_count = 0

    held_out_result = evaluate_parameterized_on_held_out(
        pcomps, held_out,
        n_programs=20, program_length=4,
        n_iterations=2, n_per_iter=12, seed=42,
    )

    print(f"{'Problem':<12} {'Alpha':<8} {'Param':<12} {'Random':<12} {'Beats':<8}")
    print("-" * 55)
    for r in held_out_result["results"]:
        b = "✓" if r["beats_random"] else "✗"
        print(f"{r['domain']:<12} {r['alpha']:<8.3f} {r['param_best']:>+12.4f} "
              f"{r['random_best']:>+12.4f} {b:<8}")

    n_beats = held_out_result["n_beats_random"]
    print()
    print(f"Parameterized DSL beats RANDOM on {n_beats}/{held_out_result['n_total']} held-out")

    # Phase 3: Compare to L5b.1 (fixed composites) baseline
    print()
    print("=" * 90)
    print("COMPARISON: L5b.1 (fixed) vs L5b.2 (parameterized)")
    print("=" * 90)
    print()

    # L5b.1 baseline: fixed composites (cycle 234-235 result = 8.6/10 multi-seed)
    from scripts.l5b_synthesis import OperatorSynthesizer
    from scripts.l5b_synthesis_heldout import evaluate_on_held_out_with_composites

    fixed_syn = OperatorSynthesizer(
        n_programs=30, program_length=4,
        n_iterations=2, n_per_iter=12,
        min_pair_frequency=1,
    )
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        fixed_syn.synthesize(training, seed=42)

    fixed_composites = fixed_syn.composites
    for c in fixed_composites:
        c.selection_count = 0

    with redirect_stdout(f):
        fixed_result = evaluate_on_held_out_with_composites(
            fixed_composites, held_out,
            n_programs=20, program_length=4,
            n_iterations=2, n_per_iter=12, seed=42,
        )

    print(f"{'Method':<30} {'Composites':<12} {'Held-out beats':<15}")
    print("-" * 60)
    print(f"{'L5b.1 (fixed composites)':<30} {len(fixed_composites):<12} "
          f"{fixed_result['n_beats_random']}/{fixed_result['n_total']:<15}")
    print(f"{'L5b.2 (parameterized)':<30} {len(pcomps):<12} "
          f"{n_beats}/{held_out_result['n_total']:<15}")

    print()
    print("=" * 90)
    print("HONEST INTERPRETATION")
    print("=" * 90)
    print()

    fixed_beats = fixed_result["n_beats_random"]
    param_beats = n_beats

    if param_beats > fixed_beats:
        print(f"PARAMETERIZED BEATS FIXED: {param_beats} vs {fixed_beats}")
        print("The learned alpha adds value! The operator's adaptive behavior")
        print("captures information that fixed composites cannot.")
        print()
        print("This is L5b.2 PROGRESS: parameterized composites are a qualitatively")
        print("new primitive type (narrow_iqr(0.4) ≠ narrow_iqr(0.8)).")
    elif param_beats == fixed_beats:
        print(f"PARAMETERIZED MATCHES FIXED: {param_beats} vs {fixed_beats}")
        print("The learned alpha does NOT add value on this benchmark.")
        print()
        print("Honest assessment: the alpha parameter doesn't capture useful")
        print("information beyond what fixed composites already provide.")
        print("The saturation ceiling persists — parameterization alone is")
        print("insufficient to break it.")
    else:
        print(f"PARAMETERIZED WORSE THAN FIXED: {param_beats} vs {fixed_beats}")
        print("The alpha parameter may be HURTING — adapting narrowing strength")
        print("to landscape stats may be counterproductive on some problems.")

    print()
    print("HONEST LABEL (enforced by test): 'parameterized' NOT 'discovered'")
    print("The underlying operators are existing DSL primitives. The innovation")
    print("is the LEARNED PARAMETER (alpha), not new algorithmic structure.")


if __name__ == "__main__":
    main()
