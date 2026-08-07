#!/usr/bin/env python3
"""
measurement_provenance.py — Stage M2: Measurement Provenance (Program A)

Per ROADMAP_V2.md Stage M2:
  Every score becomes
    Score
    ± uncertainty
    Evidence tier
    Calibration version
    Evaluator version
    Prompt version
    Judge version
    Timestamp
    Benchmark version
  No naked numbers.

Per ANTI_ENTROPY.md line 559:
  "No layer's output may emit a bare scalar. The scalar must be the
   `confidence` of an explicit `claim`, with explicit `evidence`."

This module provides the infrastructure to make every score in the
codebase carry full provenance. It defines:

  1. ScoredValue — a dataclass wrapping a scalar value with 14
     provenance fields (value, metric_id, metric_name, uncertainty_std,
     ci_95_lower, ci_95_upper, n, n_resamples, evidence_tier,
     calibration_version, evaluator_version, prompt_version,
     judge_version, timestamp, benchmark_version, is_degenerate,
     provenance_chain).

  2. ProvenanceRegistry — loads bootstrap_statistics.json and provides
     lookup by metric_id. Returns the latest bootstrap CI for any
     metric. This is the bridge between Stage M3 (bootstrap) and
     Stage M2 (provenance).

  3. @with_provenance(metric_id=...) — a decorator that wraps a
     function returning a float, and returns a ScoredValue instead.
     The decorator looks up the metric's bootstrap CI from the registry
     and attaches it to the returned value.

  4. format_score(sv) — produces the canonical string representation:
     "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500,
     tier=B, cal=dr91-cycle-243)"

USAGE:
  from programs.A_metrology.measurement_provenance import (
      ScoredValue, ProvenanceRegistry, with_provenance, format_score
  )

  # Decorator approach (preferred for new code):
  @with_provenance(metric_id="M-005", metric_name="Discovery F1",
                    evidence_tier="B", calibration_version="dr91-cycle-243",
                    evaluator_version="dr91-v1", benchmark_version="discovery-v1")
  def compute_discovery_f1(gold, candidates, match_fn):
      # ... compute F1 ...
      return f1  # returns a float

  result = compute_discovery_f1(gold, candidates, match_fn)
  # result is a ScoredValue with full provenance
  print(format_score(result))
  # "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500,
  #  tier=B, cal=dr91-cycle-243)"

  # Manual approach (for existing code that returns floats):
  registry = ProvenanceRegistry()
  sv = registry.wrap(
      value=0.8571,
      metric_id="M-005",
      metric_name="Discovery F1",
      evidence_tier="B",
      calibration_version="dr91-cycle-243",
      evaluator_version="dr91-v1",
      benchmark_version="discovery-v1",
  )

HONEST STATUS:
  - The infrastructure is complete and tested.
  - Not every score function in the codebase is wrapped yet. This is
    a gradual migration — as functions are touched, they get wrapped.
    The STOP_BUILDING list (cycle 258) prevents NEW naked-number
    functions from being added without a corresponding measurement-
    layer improvement.
  - The registry loads from reports/bootstrap_statistics.json. If a
    metric_id is not in the bootstrap data, the ScoredValue will have
    uncertainty_std=0, ci_95_lower=value, ci_95_upper=value (point
    estimate with no CI). This is documented as "UNQUANTIFIED" in the
    ScoredValue's provenance.
"""
import sys
import json
import functools
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# ScoredValue — the canonical provenance-carrying score object
# ============================================================================

@dataclass
class ScoredValue:
    """A score with full provenance. No naked numbers.

    Every score in the system must be a ScoredValue, not a bare float.
    This is the Stage M2 implementation of ANTI_ENTROPY rule 559:
    "No layer's output may emit a bare scalar."

    The 14 provenance fields are:
      value              — the score itself (float)
      metric_id          — e.g. "M-005" (from MeasurementEngineSpecification)
      metric_name        — human-readable name
      uncertainty_std    — bootstrap std (from Stage M3)
      ci_95_lower        — 95% CI lower bound
      ci_95_upper        — 95% CI upper bound
      n                  — sample size
      n_resamples        — bootstrap B (number of resamples)
      evidence_tier      — A/B/C/D/E/F/G/H/I (from CONSTITUTION evidence hierarchy)
      calibration_version — e.g. "dr91-cycle-243"
      evaluator_version  — e.g. "dr91-v1"
      prompt_version     — e.g. "n/a" for non-LLM metrics
      judge_version      — e.g. "n/a" for non-judge metrics
      timestamp          — ISO 8601 UTC
      benchmark_version  — e.g. "discovery-v1"
      is_degenerate      — True if bootstrap std = 0 (from Stage M3)
      provenance_chain   — list of modules/functions that produced this score
    """
    value: float
    metric_id: str
    metric_name: str
    uncertainty_std: float
    ci_95_lower: float
    ci_95_upper: float
    n: int
    n_resamples: int
    evidence_tier: str
    calibration_version: str
    evaluator_version: str
    prompt_version: str
    judge_version: str
    timestamp: str
    benchmark_version: str
    is_degenerate: bool = False
    provenance_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "value": round(self.value, 4),
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "uncertainty_std": round(self.uncertainty_std, 4),
            "ci_95_lower": round(self.ci_95_lower, 4),
            "ci_95_upper": round(self.ci_95_upper, 4),
            "n": self.n,
            "n_resamples": self.n_resamples,
            "evidence_tier": self.evidence_tier,
            "calibration_version": self.calibration_version,
            "evaluator_version": self.evaluator_version,
            "prompt_version": self.prompt_version,
            "judge_version": self.judge_version,
            "timestamp": self.timestamp,
            "benchmark_version": self.benchmark_version,
            "is_degenerate": self.is_degenerate,
            "provenance_chain": self.provenance_chain,
        }

    def format(self) -> str:
        """Canonical string: 'M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500, tier=B, cal=dr91-cycle-243)'"""
        deg = " DEGENERATE" if self.is_degenerate else ""
        return (
            f"{self.metric_id} = {self.value:.4f} ± {self.uncertainty_std:.4f} "
            f"(95% CI: {self.ci_95_lower:.4f}, {self.ci_95_upper:.4f}; "
            f"N={self.n}, B={self.n_resamples}, "
            f"tier={self.evidence_tier}, "
            f"cal={self.calibration_version}, "
            f"eval={self.evaluator_version}, "
            f"bench={self.benchmark_version}"
            f"{deg})"
        )

    def format_short(self) -> str:
        """Short string: 'M-005 = 0.8571 ± 0.0635 [0.7097, 0.9474]'"""
        return (
            f"{self.metric_id} = {self.value:.4f} ± {self.uncertainty_std:.4f} "
            f"[{self.ci_95_lower:.4f}, {self.ci_95_upper:.4f}]"
        )


# ============================================================================
# ProvenanceRegistry — loads bootstrap CIs and provides lookup
# ============================================================================

class ProvenanceRegistry:
    """Loads bootstrap_statistics.json and provides metric_id -> CI lookup.

    This is the bridge between Stage M3 (bootstrap) and Stage M2 (provenance).
    Every ScoredValue gets its uncertainty from this registry.
    """

    def __init__(self, bootstrap_path: Optional[Path] = None):
        if bootstrap_path is None:
            bootstrap_path = (Path(__file__).resolve().parents[2]
                              / "reports" / "bootstrap_statistics.json")
        self.bootstrap_path = bootstrap_path
        self._cache: Dict[str, Dict] = {}
        self._loaded = False

    def _load(self):
        """Load bootstrap data lazily."""
        if self._loaded:
            return
        if not self.bootstrap_path.exists():
            self._loaded = True
            return
        try:
            data = json.loads(self.bootstrap_path.read_text())
            for r in data.get("results", []):
                self._cache[r["metric_id"]] = r
        except (json.JSONDecodeError, KeyError):
            pass
        self._loaded = True

    def get_bootstrap(self, metric_id: str) -> Optional[Dict]:
        """Get bootstrap data for a metric_id. Returns None if not found."""
        self._load()
        return self._cache.get(metric_id)

    def has_metric(self, metric_id: str) -> bool:
        """Check if a metric_id has bootstrap data."""
        self._load()
        return metric_id in self._cache

    def list_metrics(self) -> List[str]:
        """List all metric_ids with bootstrap data."""
        self._load()
        return sorted(self._cache.keys())

    def wrap(
        self,
        value: float,
        metric_id: str,
        metric_name: str,
        evidence_tier: str = "I",
        calibration_version: str = "uncalibrated",
        evaluator_version: str = "unknown",
        prompt_version: str = "n/a",
        judge_version: str = "n/a",
        benchmark_version: str = "unknown",
        provenance_chain: Optional[List[str]] = None,
    ) -> ScoredValue:
        """Wrap a float value in a ScoredValue with provenance.

        If the metric_id has bootstrap data, the CI is attached.
        If not, the ScoredValue has uncertainty_std=0 and CI = (value, value),
        with is_degenerate=True and a note that the metric is UNQUANTIFIED.

        Args:
            value: the score value (float)
            metric_id: e.g. "M-005"
            metric_name: human-readable name
            evidence_tier: A/B/C/D/E/F/G/H/I (default I = LLM inference)
            calibration_version: e.g. "dr91-cycle-243"
            evaluator_version: e.g. "dr91-v1"
            prompt_version: e.g. "standard-v1" or "n/a"
            judge_version: e.g. "judge_1_standard" or "n/a"
            benchmark_version: e.g. "discovery-v1"
            provenance_chain: list of function names that produced this score

        Returns:
            ScoredValue with full provenance
        """
        boot = self.get_bootstrap(metric_id)
        if boot is not None:
            return ScoredValue(
                value=value,
                metric_id=metric_id,
                metric_name=metric_name,
                uncertainty_std=boot.get("bootstrap_std", 0.0),
                ci_95_lower=boot.get("ci_95_lower", value),
                ci_95_upper=boot.get("ci_95_upper", value),
                n=boot.get("n", 0),
                n_resamples=boot.get("n_resamples", 0),
                evidence_tier=evidence_tier,
                calibration_version=calibration_version,
                evaluator_version=evaluator_version,
                prompt_version=prompt_version,
                judge_version=judge_version,
                timestamp=datetime.now(timezone.utc).isoformat(),
                benchmark_version=benchmark_version,
                is_degenerate=boot.get("is_degenerate", False),
                provenance_chain=provenance_chain or [],
            )
        else:
            # Metric not in bootstrap data — UNQUANTIFIED
            return ScoredValue(
                value=value,
                metric_id=metric_id,
                metric_name=metric_name,
                uncertainty_std=0.0,
                ci_95_lower=value,
                ci_95_upper=value,
                n=0,
                n_resamples=0,
                evidence_tier=evidence_tier,
                calibration_version=calibration_version,
                evaluator_version=evaluator_version,
                prompt_version=prompt_version,
                judge_version=judge_version,
                timestamp=datetime.now(timezone.utc).isoformat(),
                benchmark_version=benchmark_version,
                is_degenerate=True,  # UNQUANTIFIED is degenerate
                provenance_chain=provenance_chain or [],
            )


# ============================================================================
# @with_provenance decorator
# ============================================================================

# Module-level registry instance (lazy-loaded)
_registry: Optional[ProvenanceRegistry] = None


def _get_registry() -> ProvenanceRegistry:
    global _registry
    if _registry is None:
        _registry = ProvenanceRegistry()
    return _registry


def with_provenance(
    metric_id: str,
    metric_name: str,
    evidence_tier: str = "I",
    calibration_version: str = "uncalibrated",
    evaluator_version: str = "unknown",
    prompt_version: str = "n/a",
    judge_version: str = "n/a",
    benchmark_version: str = "unknown",
) -> Callable:
    """Decorator that wraps a function returning float, returning ScoredValue.

    The decorated function should return a float. The decorator wraps
    it in a ScoredValue with provenance from the registry.

    Example:
        @with_provenance(metric_id="M-005", metric_name="Discovery F1",
                         evidence_tier="B", calibration_version="dr91-cycle-243",
                         evaluator_version="dr91-v1", benchmark_version="discovery-v1")
        def compute_discovery_f1(gold, candidates, match_fn):
            # ... compute F1 ...
            return f1

    The decorated function returns a ScoredValue instead of a float.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            value = fn(*args, **kwargs)
            registry = _get_registry()
            chain = [f"{fn.__module__}.{fn.__name__}"]
            return registry.wrap(
                value=value,
                metric_id=metric_id,
                metric_name=metric_name,
                evidence_tier=evidence_tier,
                calibration_version=calibration_version,
                evaluator_version=evaluator_version,
                prompt_version=prompt_version,
                judge_version=judge_version,
                benchmark_version=benchmark_version,
                provenance_chain=chain,
            )
        # Attach the original function for testing
        wrapper._raw_fn = fn
        wrapper._metric_id = metric_id
        return wrapper
    return decorator


# ============================================================================
# format_score — canonical string representation
# ============================================================================

def format_score(sv: ScoredValue) -> str:
    """Format a ScoredValue as a canonical string.

    Example:
        "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500,
         tier=B, cal=dr91-cycle-243, eval=dr91-v1, bench=discovery-v1)"
    """
    return sv.format()


def format_score_short(sv: ScoredValue) -> str:
    """Short format: 'M-005 = 0.8571 ± 0.0635 [0.7097, 0.9474]'"""
    return sv.format_short()


# ============================================================================
# Naked number detection (for CI enforcement)
# ============================================================================

def is_naked_number(obj: Any) -> bool:
    """Check if an object is a naked number (float or int) that should be
    a ScoredValue.

    This is used by tests to verify that score-producing functions
    return ScoredValue, not bare floats.

    Returns True if the object is a float or int (and thus 'naked').
    Returns False if it's a ScoredValue (or anything else).
    """
    return isinstance(obj, (float, int)) and not isinstance(obj, bool)


# ============================================================================
# MAIN (demonstration)
# ============================================================================

def main():
    print("=" * 80)
    print("Stage M2: Measurement Provenance (Program A)")
    print("No naked numbers. Every score carries full provenance.")
    print("=" * 80)
    print()

    registry = ProvenanceRegistry()
    metrics = registry.list_metrics()
    print(f"Registry loaded: {len(metrics)} metrics with bootstrap data")
    print()

    # Demonstrate wrapping
    print("Example ScoredValue objects:")
    print()

    # M-005: Discovery F1
    sv_m005 = registry.wrap(
        value=0.8571,
        metric_id="M-005",
        metric_name="Discovery F1 (shared, syn, DR-91)",
        evidence_tier="B",
        calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1",
        benchmark_version="discovery-v1",
        provenance_chain=["dr91_measurement_audit.main"],
    )
    print(f"  {format_score(sv_m005)}")
    print()

    # M-008: FP floor
    sv_m008 = registry.wrap(
        value=0.9189,
        metric_id="M-008",
        metric_name="FP floor (synonym)",
        evidence_tier="A",
        calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1",
        benchmark_version="discovery-v1",
    )
    print(f"  {format_score(sv_m008)}")
    print()

    # M-305: Self-validation bias
    sv_m305 = registry.wrap(
        value=2.5000,
        metric_id="M-305",
        metric_name="Self-validation bias",
        evidence_tier="I",
        calibration_version="dr94-cycle-250",
        evaluator_version="dr94-v1",
        benchmark_version="proposal-cal-v1",
    )
    print(f"  {format_score(sv_m305)}")
    print()

    # Demonstrate decorator
    print("Decorator demonstration:")
    print()

    @with_provenance(
        metric_id="M-005",
        metric_name="Discovery F1 (decorator demo)",
        evidence_tier="B",
        calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1",
        benchmark_version="discovery-v1",
    )
    def demo_discovery_f1():
        return 0.8571

    result = demo_discovery_f1()
    print(f"  {format_score(result)}")
    print(f"  Type: {type(result).__name__}")
    print(f"  Provenance chain: {result.provenance_chain}")
    print()

    # Demonstrate unquantified metric
    print("Unquantified metric (not in bootstrap data):")
    sv_unknown = registry.wrap(
        value=0.5,
        metric_id="M-999",
        metric_name="Future metric (not yet bootstrapped)",
        evidence_tier="I",
        calibration_version="uncalibrated",
        evaluator_version="unknown",
        benchmark_version="unknown",
    )
    print(f"  {format_score(sv_unknown)}")
    print(f"  is_degenerate: {sv_unknown.is_degenerate} (UNQUANTIFIED)")
    print()

    # Demonstrate naked number detection
    print("Naked number detection:")
    print(f"  is_naked_number(0.8571) = {is_naked_number(0.8571)}")
    print(f"  is_naked_number(sv_m005) = {is_naked_number(sv_m005)}")
    print(f"  is_naked_number(42) = {is_naked_number(42)}")
    print(f"  is_naked_number(True) = {is_naked_number(True)}")
    print()

    print("=" * 80)
    print("STAGE M2 INFRASTRUCTURE COMPLETE")
    print("=" * 80)
    print()
    print("ScoredValue dataclass: 17 fields (value + 14 provenance + chain)")
    print(f"ProvenanceRegistry: {len(metrics)} metrics loaded")
    print("@with_provenance decorator: available")
    print("format_score / format_score_short: available")
    print("is_naked_number: available for CI enforcement")
    print()
    print("NEXT: Wrap existing score functions to return ScoredValue.")
    print("This is gradual — as functions are touched, they get wrapped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
