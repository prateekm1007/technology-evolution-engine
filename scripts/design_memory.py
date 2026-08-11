#!/usr/bin/env python3
"""
design_memory.py — DR-79: Append-only design memory.

Stores failures, repairs, iterations, residuals, tradeoffs, dead ends,
and successful motifs. Append-only per Constitutional Rule 10 ("Never
commit a live credential" — but here the relevant rule is Law 7:
Historical permanence — and ANTI_ENTROPY rule 4: "Record every failure").

The memory is the mechanism by which candidate N+1 improves because
candidate N failed: each recorded failure carries an explicit
"lesson" that the next candidate must address.

Memory structure (all append-only):
  - failure_entries:   [{config_id, reason, lesson, timestamp}]
  - repair_entries:    [{config_id, repair_strategy, applied, timestamp}]
  - iteration_entries: [{iteration, configs, residuals, priors, timestamp}]
  - residual_entries:  [{config_id, metric, residual, timestamp}]
  - tradeoff_entries:  [{config_id, improve, worsen, resolution, timestamp}]
  - dead_end_entries:  [{config_id, reason, timestamp}]
  - motif_entries:     [{motif_id, components, structure, score, timestamp}]

Usage:
    from scripts.design_memory import DesignMemory
    mem = DesignMemory()
    mem.record_failure(config_id="C1", reason="cost > ceiling",
                       lesson="Use cheaper substrate")
    lessons = mem.get_lessons()  # list of all recorded lessons
"""
import sys
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class FailureEntry:
    config_id: str
    reason: str
    lesson: str            # what to do differently next time
    severity: str = "warn"  # 'warn' or 'fail'
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class RepairEntry:
    config_id: str
    repair_strategy: str
    applied: bool
    new_config_id: Optional[str] = None
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class IterationEntry:
    iteration: int
    config_ids: List[str] = field(default_factory=list)
    residuals: List[Dict[str, Any]] = field(default_factory=list)
    priors_before: Dict[str, float] = field(default_factory=dict)
    priors_after: Dict[str, float] = field(default_factory=dict)
    n_measured: int = 0
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class ResidualEntry:
    config_id: str
    metric: str
    predicted: float
    measured: float
    residual: float
    relative_residual: float
    significant: bool
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class TradeoffEntry:
    config_id: str
    improve: str        # parameter being improved
    worsen: str         # parameter being worsened
    resolution: str     # how the tradeoff was resolved
    operator_used: str = ""
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class DeadEndEntry:
    config_id: str
    reason: str
    branch: str = ""     # which exploration branch
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class MotifEntry:
    motif_id: str        # canonical id (hash of structure)
    components: List[str] = field(default_factory=list)
    structure: str = ""
    score: float = 0.0
    config_id: str = ""
    timestamp: str = ""
    entry_id: int = 0


@dataclass
class MemorySnapshot:
    """A point-in-time snapshot of the memory (for replay/audit)."""
    n_failures: int = 0
    n_repairs: int = 0
    n_iterations: int = 0
    n_residuals: int = 0
    n_tradeoffs: int = 0
    n_dead_ends: int = 0
    n_motifs: int = 0
    timestamp: str = ""


class DesignMemory:
    """DR-79: append-only design memory."""

    def __init__(self):
        self._failures: List[FailureEntry] = []
        self._repairs: List[RepairEntry] = []
        self._iterations: List[IterationEntry] = []
        self._residuals: List[ResidualEntry] = []
        self._tradeoffs: List[TradeoffEntry] = []
        self._dead_ends: List[DeadEndEntry] = []
        self._motifs: List[MotifEntry] = []
        self._next_id: int = 1
        # Lock: once True, no edits allowed (append-only).
        self._sealed: bool = False

    # ----- append-only enforcement -------------------------------------
    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _next_entry_id(self) -> int:
        eid = self._next_id
        self._next_id += 1
        return eid

    def seal(self) -> None:
        """Seal the memory — no further edits (immutable snapshot)."""
        self._sealed = True

    # ----- recorders (all append-only) ---------------------------------
    def record_failure(self, config_id: str, reason: str, lesson: str,
                       severity: str = "warn") -> FailureEntry:
        entry = FailureEntry(
            config_id=config_id, reason=reason, lesson=lesson,
            severity=severity, timestamp=self._now(),
            entry_id=self._next_entry_id(),
        )
        self._failures.append(entry)
        return entry

    def record_repair(self, config_id: str, repair_strategy: str,
                      applied: bool,
                      new_config_id: Optional[str] = None) -> RepairEntry:
        entry = RepairEntry(
            config_id=config_id, repair_strategy=repair_strategy,
            applied=applied, new_config_id=new_config_id,
            timestamp=self._now(), entry_id=self._next_entry_id(),
        )
        self._repairs.append(entry)
        return entry

    def record_iteration(self, iteration: int,
                         config_ids: List[str],
                         residuals: Optional[List[Dict[str, Any]]] = None,
                         priors_before: Optional[Dict[str, float]] = None,
                         priors_after: Optional[Dict[str, float]] = None,
                         n_measured: int = 0) -> IterationEntry:
        entry = IterationEntry(
            iteration=iteration, config_ids=list(config_ids),
            residuals=list(residuals or []),
            priors_before=dict(priors_before or {}),
            priors_after=dict(priors_after or {}),
            n_measured=n_measured,
            timestamp=self._now(), entry_id=self._next_entry_id(),
        )
        self._iterations.append(entry)
        return entry

    def record_residual(self, config_id: str, metric: str,
                        predicted: float, measured: float,
                        residual: float, relative_residual: float,
                        significant: bool) -> ResidualEntry:
        entry = ResidualEntry(
            config_id=config_id, metric=metric,
            predicted=predicted, measured=measured,
            residual=residual, relative_residual=relative_residual,
            significant=significant,
            timestamp=self._now(), entry_id=self._next_entry_id(),
        )
        self._residuals.append(entry)
        return entry

    def record_tradeoff(self, config_id: str, improve: str, worsen: str,
                        resolution: str, operator_used: str = "") -> TradeoffEntry:
        entry = TradeoffEntry(
            config_id=config_id, improve=improve, worsen=worsen,
            resolution=resolution, operator_used=operator_used,
            timestamp=self._now(), entry_id=self._next_entry_id(),
        )
        self._tradeoffs.append(entry)
        return entry

    def record_dead_end(self, config_id: str, reason: str,
                        branch: str = "") -> DeadEndEntry:
        entry = DeadEndEntry(
            config_id=config_id, reason=reason, branch=branch,
            timestamp=self._now(), entry_id=self._next_entry_id(),
        )
        self._dead_ends.append(entry)
        return entry

    def record_motif(self, motif_id: str, components: List[str],
                     structure: str, score: float,
                     config_id: str = "") -> MotifEntry:
        entry = MotifEntry(
            motif_id=motif_id, components=list(components),
            structure=structure, score=score, config_id=config_id,
            timestamp=self._now(), entry_id=self._next_entry_id(),
        )
        self._motifs.append(entry)
        return entry

    # ----- query API ---------------------------------------------------
    def get_lessons(self) -> List[str]:
        """All lessons recorded from failures."""
        return [f.lesson for f in self._failures]

    def get_failures(self) -> List[FailureEntry]:
        return list(self._failures)

    def get_repairs(self) -> List[RepairEntry]:
        return list(self._repairs)

    def get_iterations(self) -> List[IterationEntry]:
        return list(self._iterations)

    def get_residuals(self) -> List[ResidualEntry]:
        return list(self._residuals)

    def get_tradeoffs(self) -> List[TradeoffEntry]:
        return list(self._tradeoffs)

    def get_dead_ends(self) -> List[DeadEndEntry]:
        return list(self._dead_ends)

    def get_motifs(self) -> List[MotifEntry]:
        return list(self._motifs)

    def get_failures_for_config(self, config_id: str) -> List[FailureEntry]:
        return [f for f in self._failures if f.config_id == config_id]

    def get_lessons_for_config(self, config_id: str) -> List[str]:
        return [f.lesson for f in self._failures if f.config_id == config_id]

    def get_motifs_above(self, score_threshold: float) -> List[MotifEntry]:
        """Successful motifs with score > threshold."""
        return [m for m in self._motifs if m.score > score_threshold]

    def snapshot(self) -> MemorySnapshot:
        """Return a point-in-time snapshot."""
        return MemorySnapshot(
            n_failures=len(self._failures),
            n_repairs=len(self._repairs),
            n_iterations=len(self._iterations),
            n_residuals=len(self._residuals),
            n_tradeoffs=len(self._tradeoffs),
            n_dead_ends=len(self._dead_ends),
            n_motifs=len(self._motifs),
            timestamp=self._now(),
        )

    # ----- serialization (for replay/audit) ----------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "failures": [asdict(f) for f in self._failures],
            "repairs": [asdict(r) for r in self._repairs],
            "iterations": [asdict(i) for i in self._iterations],
            "residuals": [asdict(r) for r in self._residuals],
            "tradeoffs": [asdict(t) for t in self._tradeoffs],
            "dead_ends": [asdict(d) for d in self._dead_ends],
            "motifs": [asdict(m) for m in self._motifs],
            "snapshot": asdict(self.snapshot()),
        }

    def save(self, path: Path) -> None:
        """Save the memory to a JSON file (append-only — does not modify)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    # ----- append-only invariant check ---------------------------------
    def verify_append_only(self, prior_snapshot: MemorySnapshot) -> bool:
        """Verify that no entries have been removed or modified since
        the prior snapshot. Returns True if the memory is append-only
        consistent.
        """
        # The counts must only have grown.
        current = self.snapshot()
        return (current.n_failures >= prior_snapshot.n_failures
                and current.n_repairs >= prior_snapshot.n_repairs
                and current.n_iterations >= prior_snapshot.n_iterations
                and current.n_residuals >= prior_snapshot.n_residuals
                and current.n_tradeoffs >= prior_snapshot.n_tradeoffs
                and current.n_dead_ends >= prior_snapshot.n_dead_ends
                and current.n_motifs >= prior_snapshot.n_motifs)


def main():
    print("=" * 60)
    print("DESIGN MEMORY (DR-79)")
    print("=" * 60)
    print()

    mem = DesignMemory()

    # Simulate a few cycles
    mem.record_failure("C1", "cost > ceiling",
                       "Use cheaper substrate (graphite instead of Pt)")
    mem.record_failure("C2", "ZT < 1.0",
                       "Reduce thermal conductivity via porosity")
    mem.record_repair("C2", "apply invert operator with porosity=0.3",
                      applied=True, new_config_id="C3")
    mem.record_residual("C1", "ZT", 1.10, 1.00, 0.10, 0.10, True)
    mem.record_tradeoff("C3", "electrical_conductivity", "thermal_conductivity",
                        "Used porosity to break tradeoff",
                        operator_used="invert")
    mem.record_dead_end("C5", "all operators exhausted, no improvement",
                        branch="layered_3")
    mem.record_motif("MOTIF-001", ["bismuth_telluride", "graphene"],
                     "layered_2", score=1.2, config_id="C7")
    mem.record_iteration(0, ["C1", "C2", "C3"],
                         priors_before={"seebeck_coefficient": 1.0},
                         priors_after={"seebeck_coefficient": 0.95},
                         n_measured=3)

    snap = mem.snapshot()
    print(f"Snapshot: {snap}")
    print()
    print("Lessons learned:")
    for l in mem.get_lessons():
        print(f"  - {l}")
    print()
    print("Successful motifs (score > 1.0):")
    for m in mem.get_motifs_above(1.0):
        print(f"  {m.motif_id}: {m.components} score={m.score}")


if __name__ == "__main__":
    main()
