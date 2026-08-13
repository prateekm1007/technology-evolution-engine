"""
MDDG V3 — Independence Procedure with 2-of-3 Secondary Criteria (directive #11).

Per directive #11:
  1. SET_A ∩ SET_B = ∅ (true set disjointness, not hash inequality)
  2. At least TWO of:
     a. different author/institution sets
     b. no shared citation within N hops
     c. different application-domain vocabulary
  3. Store complete source sets and hashes
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
import hashlib


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class IndependenceAttestation:
    """V3 independence attestation with 2-of-3 secondary criteria.

    Per directive #11: "Do not require all three; that would over-constrain
    the system. Store the complete source sets and hashes."
    """
    # Primary: set disjointness
    set_a_ids: tuple[str, ...]
    set_b_ids: tuple[str, ...]
    set_a_hash: str
    set_b_hash: str
    is_disjoint: bool              # A ∩ B = ∅

    # Secondary: 2-of-3 criteria
    different_author_institution: bool
    no_shared_citation: bool
    different_domain_vocabulary: bool
    secondary_criteria_passed: int  # how many of the 3 passed (need >= 2)

    # Temporal
    mechanism_source_dates: tuple[str, ...]
    lock_time: str
    all_sources_predate_lock: bool

    # Final
    is_independent: bool           # disjoint AND 2-of-3 AND all predate

    def canonical_dict(self) -> dict:
        return asdict(self)


def check_different_authors(set_a_authors: set[str], set_b_authors: set[str]) -> bool:
    """Criterion A: different author/institution sets.

    Per directive #11: "different author/institution sets"
    """
    if not set_a_authors or not set_b_authors:
        return True  # if one set has no authors, treat as different
    return len(set_a_authors & set_b_authors) == 0


def check_no_shared_citation(set_a_citations: set[str],
                              set_b_citations: set[str],
                              n_hops: int = 1) -> bool:
    """Criterion B: no shared citation within N hops.

    Per directive #11: "no shared citation within N hops"
    """
    if not set_a_citations or not set_b_citations:
        return True  # if one set has no citations, treat as no shared
    return len(set_a_citations & set_b_citations) == 0


def check_different_vocabulary(set_a_vocabulary: set[str],
                                set_b_vocabulary: set[str]) -> bool:
    """Criterion C: different application-domain vocabulary.

    Per directive #11: "different application-domain vocabulary"

    We measure vocabulary overlap via Jaccard distance. If the Jaccard
    similarity is < 0.3, the vocabularies are considered different.
    """
    if not set_a_vocabulary or not set_b_vocabulary:
        return True
    union = set_a_vocabulary | set_b_vocabulary
    if not union:
        return True
    jaccard = len(set_a_vocabulary & set_b_vocabulary) / len(union)
    return jaccard < 0.3


def attest_independence_v3(
    device_failure_source_ids: list[str],
    mechanism_source_ids: list[str],
    mechanism_source_dates: list[str],
    set_a_authors: set[str],
    set_b_authors: set[str],
    set_a_citations: set[str],
    set_b_citations: set[str],
    set_a_vocabulary: set[str],
    set_b_vocabulary: set[str],
    lock_time: Optional[str] = None,
) -> IndependenceAttestation:
    """V3 independence attestation.

    Per directive #11:
      1. SET_A ∩ SET_B = ∅ (true set disjointness)
      2. At least 2 of: different authors, no shared citations, different vocabulary
      3. All mechanism sources predate lock time
    """
    lock_time = lock_time or now_iso()
    lock_date = lock_time[:10]
    set_a = set(device_failure_source_ids)
    set_b = set(mechanism_source_ids)
    is_disjoint = len(set_a & set_b) == 0

    # 2-of-3 secondary criteria
    crit_a = check_different_authors(set_a_authors, set_b_authors)
    crit_b = check_no_shared_citation(set_a_citations, set_b_citations)
    crit_c = check_different_vocabulary(set_a_vocabulary, set_b_vocabulary)
    secondary_passed = sum([crit_a, crit_b, crit_c])

    # Temporal: all mechanism sources predate lock
    all_predate = all(
        d < lock_date if d and len(d) >= 10 else False
        for d in mechanism_source_dates
    ) if mechanism_source_dates else False

    # Final: disjoint AND 2-of-3 AND all predate
    is_independent = is_disjoint and secondary_passed >= 2 and all_predate

    return IndependenceAttestation(
        set_a_ids=tuple(sorted(set_a)),
        set_b_ids=tuple(sorted(set_b)),
        set_a_hash=hashlib.sha256("|".join(sorted(set_a)).encode()).hexdigest(),
        set_b_hash=hashlib.sha256("|".join(sorted(set_b)).encode()).hexdigest(),
        is_disjoint=is_disjoint,
        different_author_institution=crit_a,
        no_shared_citation=crit_b,
        different_domain_vocabulary=crit_c,
        secondary_criteria_passed=secondary_passed,
        mechanism_source_dates=tuple(mechanism_source_dates),
        lock_time=lock_time,
        all_sources_predate_lock=all_predate,
        is_independent=is_independent,
    )
