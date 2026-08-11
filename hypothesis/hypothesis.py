"""
Hypothesis — the atomic unit of a learning system.

Per CTO review #4 (commit `0029759`), the Hypothesis is the new
fundamental object of the system. Per CTO review #5, the schema is
extended with counterevidence, assumptions, dependencies, created_at,
updated_at. Per CTO review #6, the canonical schema is finalized
with `id` as the first field, so dependencies can reference other
Hypotheses unambiguously.

Canonical schema (per ANTI_ENTROPY.md, finalized review #6):

    id              : str             — stable identifier (hash of claim+evidence+created_at)
    claim           : str             — a falsifiable statement
    confidence      : float in [0,1] — system's prior belief, BEFORE observation
    evidence        : list[str]       — named inputs supporting the claim
    counterevidence : list[str]       — named inputs that would weaken the claim (review #5)
    assumptions     : list[str]       — preconditions the claim makes (review #5)
    dependencies    : list[str]       — IDs of other Hypotheses this one depends on (review #5)
    status          : "pending" | "pass" | "fail"
    observation     : str | None      — what was observed (None until reconciled)
    writer          : str             — module path that produced this hypothesis
    created_at      : ISO8601 UTC str
    updated_at      : ISO8601 UTC str, updated on reconcile() (review #5)

Invariants (enforced by the constructor):
  - claim must be a non-empty string.
  - confidence must be in [0, 1].
  - If evidence is empty, confidence is forced to 0.0.
  - status starts as "pending".
  - created_at and updated_at are equal at construction time.
  - id is auto-generated as a deterministic hash of
    (claim + evidence + created_at) so it is reproducible per Law 7.

Reconciliation:
  - reconcile(outcome, observation) sets status, observation, and
    bumps updated_at.
  - Once reconciled, the hypothesis is immutable. A new prediction
    requires a new Hypothesis (Law 7: historical permanence).

Backwards compatibility:
  - Old code that constructed Hypothesis without the new fields
    (counterevidence/assumptions/dependencies) still works — the
    fields default to empty lists.
  - The `timestamp` field from review #4 is preserved as an alias
    for `created_at` (deprecated; new code should use `created_at`).
  - The `id` field from review #6 is auto-generated if not provided;
    it can also be passed explicitly (e.g., when reconstructing from
    a ledger entry via from_dict).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import hashlib
import json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(claim: str, evidence: list, created_at: str) -> str:
    """Deterministic hash of (claim + evidence + created_at) per Law 7.

    The id is reproducible: two Hypotheses with the same claim,
    evidence, and created_at produce the same id. This is essential
    for dependency references — a Hypothesis that depends on another
    can reference it by id, and the id is stable across runs.
    """
    canonical = json.dumps({
        "claim": claim,
        "evidence": sorted(evidence),
        "created_at": created_at,
    }, sort_keys=True, default=str)
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"hyp_{h}"


@dataclass
class Hypothesis:
    """The atomic unit of a learning system.

    A claim with confidence and evidence, awaiting reconciliation
    with reality. Extended per CTO review #5 with counterevidence,
    assumptions, dependencies, created_at, updated_at. Finalized
    per CTO review #6 with `id` as the first field.
    """
    # `id` is the first field per the canonical schema (review #6).
    # If not provided, it is auto-generated as a stable hash.
    id: str = ""
    claim: str = ""
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    counterevidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    observation: Optional[str] = None
    writer: str = "hypothesis.hypothesis.Hypothesis"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

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
            self.confidence = max(0.0, min(1.0, self.confidence))
        # Force list fields to lists of strings.
        if self.evidence is None:
            self.evidence = []
        self.evidence = [str(e) for e in self.evidence]
        if self.counterevidence is None:
            self.counterevidence = []
        self.counterevidence = [str(e) for e in self.counterevidence]
        if self.assumptions is None:
            self.assumptions = []
        self.assumptions = [str(a) for a in self.assumptions]
        if self.dependencies is None:
            self.dependencies = []
        self.dependencies = [str(d) for d in self.dependencies]
        # CRITICAL INVARIANT: empty evidence => confidence = 0.
        if len(self.evidence) == 0:
            self.confidence = 0.0
        # Status must be valid.
        if self.status not in ("pending", "pass", "fail"):
            raise ValueError(
                f"Hypothesis.status must be pending|pass|fail, got {self.status!r}"
            )
        # created_at and updated_at should be set; if only one is,
        # copy it to the other.
        if not self.created_at:
            self.created_at = _now_iso()
        if not self.updated_at:
            self.updated_at = self.created_at
        # If id was not provided, auto-generate it as a stable hash.
        # Per review #6, the id is the first field of the canonical
        # schema and is required for dependency references.
        if not self.id:
            self.id = _stable_id(self.claim, self.evidence, self.created_at)

    def reconcile(self, outcome: str, observation: str) -> None:
        """Reconcile this hypothesis against an observation.

        Bumps updated_at. Once reconciled, the hypothesis is immutable.
        A new prediction requires a new Hypothesis (Law 7).

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
        self.updated_at = _now_iso()

    def to_dict(self) -> dict:
        """JSON-serializable representation for ledger storage.

        Includes `id` as the first field per the canonical schema
        (review #6). Includes both `created_at` and the legacy
        `timestamp` alias for backwards compatibility with review-#4
        code.
        """
        return {
            "id": self.id,
            "claim": self.claim,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "counterevidence": self.counterevidence,
            "assumptions": self.assumptions,
            "dependencies": self.dependencies,
            "status": self.status,
            "observation": self.observation,
            "writer": self.writer,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            # Backwards-compat alias (review #4 code reads `timestamp`).
            "timestamp": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Hypothesis":
        """Reconstruct a Hypothesis from a dict (e.g., from the ledger).

        Tolerates dicts written under the review-#4 schema (no
        counterevidence/assumptions/dependencies), the review-#5
        extended schema, and the review-#6 canonical schema (with id).
        """
        # created_at falls back to legacy `timestamp` field for review-#4 dicts.
        created_at = d.get("created_at") or d.get("timestamp") or _now_iso()
        return cls(
            id=d.get("id", ""),  # review #6: preserve id if provided
            claim=d["claim"],
            confidence=d["confidence"],
            evidence=d.get("evidence", []),
            counterevidence=d.get("counterevidence", []),
            assumptions=d.get("assumptions", []),
            dependencies=d.get("dependencies", []),
            status=d.get("status", "pending"),
            observation=d.get("observation"),
            writer=d.get("writer", "hypothesis.hypothesis.Hypothesis"),
            created_at=created_at,
            updated_at=d.get("updated_at", created_at),
        )

    def compose(self, other: "Hypothesis", claim: str,
                weight_self: float = 0.5) -> "Hypothesis":
        """Compose this hypothesis with another into a new hypothesis.

        The composed confidence is a weighted mean of the constituent
        confidences. The composed evidence is the union of the
        constituent evidence lists. The composed counterevidence is
        the union of the constituent counterevidence lists. The
        composed assumptions and dependencies are the union of the
        constituents'.

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
        composed_counterevidence = list(set(
            self.counterevidence + other.counterevidence))
        composed_assumptions = list(set(self.assumptions + other.assumptions))
        composed_dependencies = list(set(self.dependencies + other.dependencies))
        return Hypothesis(
            claim=claim,
            confidence=composed_confidence,
            evidence=composed_evidence,
            counterevidence=composed_counterevidence,
            assumptions=composed_assumptions,
            dependencies=composed_dependencies,
            writer="hypothesis.hypothesis.Hypothesis.compose",
        )

    # Backwards-compat property: code that read `h.timestamp` in
    # review-#4 still works in review-#5/#6.
    @property
    def timestamp(self) -> str:
        return self.created_at

