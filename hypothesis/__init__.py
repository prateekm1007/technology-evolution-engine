"""
Hypothesis package — the new fundamental object of the system.

Per CTO review #4 (commit `f590661`), the fundamental object of the
system is changing:

    document → graph → blueprint → hypothesis

A Hypothesis is the atomic unit going forward. Every layer output
is (or composes) a Hypothesis. A Hypothesis is:

    claim       — a falsifiable statement
    confidence  — a scalar in [0, 1] representing the system's prior
                  belief in the claim, BEFORE observation
    evidence    — a list of named inputs that produced the claim
    status      — "pending" (default), "pass", or "fail"
    observation — what was observed when the claim was reconciled
                  (None until reconciled)
    writer      — module path that produced this hypothesis (for
                  Law 8 replayability)
    timestamp   — ISO8601 UTC

A Hypothesis with empty evidence MUST have confidence = 0.0 — an
unsupported claim is not a claim, it's a guess.

A Hypothesis that has been reconciled carries status="pass" or
status="fail" and an observation. The reconciliation is recorded
in the verification ledger (data/ledger/predictions.jsonl) per
Law 8.

Hypotheses compose: a layer's output may be a Hypothesis whose
evidence is a list of other Hypotheses. The composite confidence
is computed from the constituent confidences (currently a simple
weighted mean; future versions may use Bayesian update).
"""
from .hypothesis import Hypothesis

__all__ = ["Hypothesis"]
