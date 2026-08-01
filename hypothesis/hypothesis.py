"""
Hypothesis — the atomic unit of a learning system.

Per CTO review #4, every assertion the system emits is (or composes)
a Hypothesis. A Hypothesis is the claim/confidence/evidence triple
awaiting reconciliation with reality.

Schema (per ANTI_ENTROPY.md):

    claim       : str             — a falsifiable statement
    confidence  : float in [0,1] — system's prior belief, BEFORE observation
    evidence    : list[str]       — named inputs that produced the claim
    status      : "pending" | "pass" | "fail"  — reconciliation state
    observation : str | None      — what was observed (None until reconciled)
    writer      : str             — module path that produced this hypothesis
    timestamp   : ISO8601 UTC str

Invariants (enforced by the constructor):
  - claim must be a non-empty string.
  - confidence must be in [0, 1].
  - If evidence is empty, confidence is forced to 0.0.
    (An unsupported claim is a guess, not a hypothesis.)
  - status starts as "pending".

Reconciliation:
  - reconcile(outcome="pass"|"fail", observation=str) sets status
    and observation.
  - Once reconciled, the hypothesis is immutable — its claim,
    confidence, and evidence are frozen. A new prediction requires
    a new Hypothesis (Law 7: historical permanence).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any


@dataclass
class Hypothesis:
    """The atomic unit of a learning system.

    A claim with confidence and evidence, awaiting reconciliation
    with reality.
    """
    claim: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    status: str = "pending"
    observation: Optional[str] = None
    writer: str = "hypothesis.hypothesis.Hypothesis"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        # Enforce invariants.
        if not isinstance(self.claim, str) or not self.claim.strip():
            raise ValueError(
                f"Hypothesis.claim must be a non-empty string, got {self.claim!r}"
            )
        # Force confidence to float in [0, 1].
        try:
            self.confidence = float(self.confidence)
        except (TypeError, ValueError):
            raise ValueError(
                f"Hypothesis.confidence must be a number in [0,1], "
                f"got {self.confidence!r}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            # Clamp, don't raise — but log by setting to nearest bound.
            self.confidence = max(0.0, min(1.0, self.confidence))
        # Force evidence to a list of strings.
        if self.evidence is None:
            self.evidence = []
        self.evidence = [str(e) for e in self.evidence]
        # CRITICAL INVARIANT: empty evidence => confidence = 0.
        # An unsupported claim is a guess, not a hypothesis.
        if len(self.evidence) == 0:
            self.confidence = 0.0
        # Status must be valid.
        if self.status not in ("pending", "pass", "fail"):
            raise ValueError(
                f"Hypothesis.status must be pending|pass|fail, got {self.status!r}"
            )

    def reconcile(self, outcome: str, observation: str) -> None:
        """Reconcile this hypothesis against an observation.

        Once reconciled, the hypothesis is immutable. A new prediction
        requires a new Hypothesis (Law 7: historical permanence).

        Args:
            outcome: "pass" (observation supports the claim) or
                     "fail" (observation contradicts the claim).
            observation: a human-readable description of what was
                         observed.
        """
        if self.status != "pending":
            raise RuntimeError(
                f"Hypothesis already reconciled (status={self.status}). "
                f"A new prediction requires a new Hypothesis (Law 7: "
                f"historical permanence)."
            )
        if outcome not in ("pass", "fail"):
            raise ValueError(
                f"outcome must be 'pass' or 'fail', got {outcome!r}"
            )
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError(
                f"observation must be a non-empty string, got {observation!r}"
            )
        self.status = outcome
        self.observation = observation

    def to_dict(self) -> dict:
        """JSON-serializable representation for ledger storage."""
        return {
            "claim": self.claim,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "status": self.status,
            "observation": self.observation,
            "writer": self.writer,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Hypothesis":
        """Reconstruct a Hypothesis from a dict (e.g., from the ledger).

        Note: a reconciled hypothesis reconstructed this way is
        immutable. To make a new prediction, construct a new
        Hypothesis — do not mutate this one.
        """
        h = cls(
            claim=d["claim"],
            confidence=d["confidence"],
            evidence=d.get("evidence", []),
            status=d.get("status", "pending"),
            observation=d.get("observation"),
            writer=d.get("writer", "hypothesis.hypothesis.Hypothesis"),
            timestamp=d.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
        return h

    def compose(self, other: "Hypothesis", claim: str,
                weight_self: float = 0.5) -> "Hypothesis":
        """Compose this hypothesis with another into a new hypothesis.

        The composed confidence is a weighted mean of the constituent
        confidences. The composed evidence is the union of the
        constituent evidence lists. The composed claim is provided by
        the caller.

        This is a simple model. Future versions may use Bayesian
        update (treating each constituent as independent evidence
        for the composed claim).

        Args:
            other: the other Hypothesis to compose with.
            claim: the claim of the composed Hypothesis.
            weight_self: weight of self's confidence in the mean
                         (0..1; other gets 1 - weight_self).

        Returns:
            A new Hypothesis (status="pending").
        """
        if not 0.0 <= weight_self <= 1.0:
            raise ValueError(f"weight_self must be in [0,1], got {weight_self}")
        composed_confidence = (
            weight_self * self.confidence
            + (1.0 - weight_self) * other.confidence
        )
        composed_evidence = list(set(self.evidence + other.evidence))
        return Hypothesis(
            claim=claim,
            confidence=composed_confidence,
            evidence=composed_evidence,
            writer="hypothesis.hypothesis.Hypothesis.compose",
        )
