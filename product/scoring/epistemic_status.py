"""
Epistemic status helper — Honesty Loop (Law 27/28/29).

Per BLUEPRINT_CONSTITUTION.md Law 27: no numerical certainty may be
assigned to claims that lack repeated experimental validation.

Per Law 29e: every claim must carry a typed status block:
    validation_level: L0-L9
    evidence_strength: ABSENT | WEAK | MODERATE | STRONG | VERY_STRONG
    experimental_validation: ABSENT | BENCH | SUBSYSTEM | PROTOTYPE | PILOT | PRODUCTION
    status: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED | PLAUSIBLE

This module provides the canonical typed status blocks for the
analyze pipeline's outputs (business report, consumer report,
blueprint). The analyzer's predictions are un-validated analytical
estimates — the honest epistemic status is L2 / WEAK / ABSENT /
PLAUSIBLE, matching the Oracle's status (oracle_deep.py).

Per Law 7 (Historical Permanence): the legacy `confidence` number
is retained as `legacy_confidence_deprecated` for one release cycle
to avoid silent breakage of downstream consumers. It will be removed
in the next cycle.
"""

# The canonical epistemic status for analyzer outputs.
# Same as ORACLE_EPISTEMIC_STATUS in oracle_deep.py — both are
# un-validated analytical estimates.
ANALYZER_EPISTEMIC_STATUS = {
    "validation_level": "L2",
    "evidence_strength": "WEAK",
    "experimental_validation": "ABSENT",
    "status": "PLAUSIBLE",
    "rationale": (
        "Analyzer predictions are analytical estimates derived from "
        "graph-structural signals (prerequisites met, constraints "
        "binding, cemetery analogues, lineage depth). No calibration "
        "data exists. No physical validation has been performed. The "
        "numerical `legacy_confidence` field is retained for backward "
        "compatibility only and MUST NOT be cited as a probability "
        "— per Law 27, it is forbidden as a claim confidence."
    ),
}


def make_epistemic_status(*, validation_level: str = "L2",
                          evidence_strength: str = "WEAK",
                          experimental_validation: str = "ABSENT",
                          status: str = "PLAUSIBLE",
                          rationale: str = None) -> dict:
    """Return a typed epistemic_status block.

    Per Law 29e, every claim must carry this block. The defaults
    match the analyzer's honest epistemic status (L2 analytical
    estimate, no experimental validation).
    """
    return {
        "validation_level": validation_level,
        "evidence_strength": evidence_strength,
        "experimental_validation": experimental_validation,
        "status": status,
        "rationale": rationale or ANALYZER_EPISTEMIC_STATUS["rationale"],
    }


def migrate_confidence_to_typed(legacy_confidence: float,
                                 *,
                                 validation_level: str = "L2",
                                 evidence_strength: str = "WEAK",
                                 experimental_validation: str = "ABSENT",
                                 status: str = "PLAUSIBLE",
                                 rationale: str = None) -> dict:
    """Convert a legacy numerical confidence to the typed status block.

    Returns a dict with:
        - epistemic_status: the typed block (Law 29e)
        - legacy_confidence_deprecated: the old number, marked DEPRECATED

    Per Law 27: the legacy number MUST NOT be used as a claim
    confidence. It is retained for one release cycle for backward
    compat with downstream consumers, then will be removed.
    """
    return {
        "epistemic_status": make_epistemic_status(
            validation_level=validation_level,
            evidence_strength=evidence_strength,
            experimental_validation=experimental_validation,
            status=status,
            rationale=rationale,
        ),
        "legacy_confidence_deprecated": round(float(legacy_confidence), 4),
    }
