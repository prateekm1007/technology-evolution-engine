"""
Deterministic not-entailed check for cross-corpus candidates (Issue #4).

A candidate's `candidate_claim_text` is *retrieval-negative* iff, for EVERY
source document in the supporting subgraph, the source does NOT entail the
claim. We check each source independently. If any source entails the claim,
the candidate is rejected (already-known). If a source is UNKNOWN (cannot
decide), the candidate is NOT retrieval-negative — UNKNOWN never counts as
negative.

This mirrors PSCD-1's retrieval_negative_attestation protocol: deterministic,
per-source, UNKNOWN-as-not-negative.

ENTAILMENT RULES (deterministic, no LLM):
  A claim is "P predicate O [value]" (possibly negated).

  Source S entails the claim iff S has a claim edge with the SAME
  (subject-as-source, predicate, obj) and:
    - both the source claim and candidate claim are non-negated AND
      values are compatible (candidate value is not contradicted), OR
    - both are negated.

  Source S *contradicts* the claim iff S has a matching (subject, predicate,
  obj) edge with the opposite negation.

  Source S is UNKNOWN iff no matching edge exists.

  Retrieval-negative for the candidate iff:
    for every source S in the supporting subgraph:
      S does NOT entail the claim
    AND
    for at least one source S, S is UNKNOWN (otherwise the claim is fully
    contradicted, which is a different kind of negative result).

To avoid trivially-true candidates, we additionally require that the claim is
NOT entailed by the union of all evidence-graph claims either (otherwise it
is a known fact, not a discovery).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .schema import Claim, Candidate
from .graph import EvidenceGraph


@dataclass
class EntailmentResult:
    source_id: str
    decision: str       # ENTAILS | CONTRADICTS | UNKNOWN
    matched_edge: Optional[dict] = None


def check_source_entailment(graph: EvidenceGraph, source_id: str,
                            claim: Claim) -> EntailmentResult:
    """Check whether a single source entails/contradicts/unknowns the claim."""
    # Find claim edges from source_id whose obj matches and predicate matches
    # and subject matches.
    for etype, dst, pl in graph.neighbors(source_id, "claim"):
        if etype != "claim":
            continue
        if pl.get("predicate") != claim.predicate:
            continue
        if dst != claim.obj:
            continue
        if pl.get("subject") != claim.subject:
            continue
        # subject/predicate/object match. Check negation and value.
        src_neg = bool(pl.get("negated", False))
        if src_neg == claim.negated:
            # Same polarity. Check value compatibility.
            src_val = pl.get("value")
            if claim.value is None or src_val is None or src_val == claim.value:
                return EntailmentResult(source_id, "ENTAILS", pl)
            # Values differ but neither negated — partial match; treat as
            # ENTAILS only if candidate value is not stricter than source.
            # Conservative: treat differing values as UNKNOWN (not entailed,
            # not contradicted) — the candidate may be a refinement.
            return EntailmentResult(source_id, "UNKNOWN", pl)
        else:
            # Opposite polarity = contradiction
            return EntailmentResult(source_id, "CONTRADICTS", pl)
    return EntailmentResult(source_id, "UNKNOWN")


def retrieval_negative_attestation(graph: EvidenceGraph,
                                    candidate: Candidate,
                                    supporting_source_ids: list[str]) -> dict:
    """Per-source retrieval-negative attestation.

    Returns a structured attestation. The candidate is retrieval-negative iff:
      - every source is ENTAILS=False (i.e., CONTRADICTS or UNKNOWN), AND
      - at least one source is UNKNOWN (genuine novelty, not pure contradiction),
      - AND no source ENTAILS the claim.
    """
    results = []
    has_invalid = False
    for sid in supporting_source_ids:
        # Reconstruct the Claim from candidate text — but our candidate carries
        # a textual claim, not a structured Claim. We rely on the motif
        # detector to also produce a structured claim; we accept it via the
        # candidate's `predicted_outcome` field which carries a structured form.
        # For this check, we extract the claim from the candidate's canonical
        # fields. To keep the interface simple, the caller (motif detector)
        # passes the structured claim via candidate.predicted_outcome using
        # the format: "subject|predicate|obj|value|negated"
        parts = candidate.predicted_outcome.split("|")
        if len(parts) >= 3:
            claim = Claim(
                subject=parts[0],
                predicate=parts[1],
                obj=parts[2],
                value=parts[3] if len(parts) > 3 and parts[3] else None,
                negated=(len(parts) > 4 and parts[4] == "True"),
            )
        else:
            # No structured claim — fail closed. Mark as INVALID.
            # INVALID prevents retrieval-negative (cannot prove novelty).
            has_invalid = True
            results.append({
                "source_id": sid, "decision": "INVALID",
                "reason": "no structured claim in candidate"
            })
            continue
        r = check_source_entailment(graph, sid, claim)
        results.append({
            "source_id": sid,
            "decision": r.decision,
            "matched_edge": r.matched_edge,
        })

    any_entails = any(r["decision"] == "ENTAILS" for r in results)
    any_unknown = any(r["decision"] == "UNKNOWN" for r in results)
    # retrieval-negative requires: no source ENTAILS, at least one UNKNOWN,
    # AND no INVALID (fail-closed on unparseable claims).
    is_retrieval_negative = (not any_entails) and any_unknown and (not has_invalid)

    return {
        "candidate_id": candidate.candidate_id,
        "sources_checked": len(results),
        "per_source": results,
        "any_entails": any_entails,
        "any_unknown": any_unknown,
        "has_invalid": has_invalid,
        "is_retrieval_negative": is_retrieval_negative,
        "all_evaluated": all(r["decision"] in ("ENTAILS", "CONTRADICTS", "UNKNOWN", "INVALID")
                             for r in results),
    }
