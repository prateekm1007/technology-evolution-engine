"""
DOCDB / INPADOC patent family normalization (Issue #4).

A DOCDB *simple family* = all publications sharing the same set of priority
documents. Members of a simple family are treated as the *same invention* for
graph purposes — they collapse to one family node.

We compute simple-family membership from the priority-chain field on each
Patent record. Two patents are in the same family iff their priority-chain
sets are identical (this matches DOCDB simple-family definition).
"""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable
from .schema import Patent, PatentFamily
import hashlib


def _priority_chain_key(patent: Patent) -> str:
    """Canonical key for the simple-family: the sorted, de-duplicated priority set.

    For pilot fixtures, `processes[0]` is overloaded to also carry the
    priority-chain string under the convention "PRIORITY_CHAIN:<dates>".
    Real ingest would populate this from EPO-OPS priority documents.
    """
    # We use a dedicated attribute if present; otherwise fall back to
    # (earliest_priority_date + assignee) as an approximation. Real ingest
    # must populate `processes` with "PRIORITY_CHAIN:..." entries.
    chain = []
    for p in patent.processes:
        if isinstance(p, str) and p.startswith("PRIORITY_CHAIN:"):
            chain.append(p)
    if chain:
        return "|".join(sorted(set(chain)))
    # Fallback approximation (clearly labelled, never used for real ingest)
    return f"APPROX:{patent.assignee or 'UNKNOWN'}:{patent.priority_date or 'NO_PRIO'}"


def normalize_families(patents: Iterable[Patent]) -> list[PatentFamily]:
    """Group patents into DOCDB simple families.

    Returns PatentFamily objects. Each patent's docdb_family_id is overwritten
    with the computed family id (canonical), so downstream code can rely on it.
    """
    groups: dict[str, list[Patent]] = defaultdict(list)
    for p in patents:
        groups[_priority_chain_key(p)].append(p)

    families: list[PatentFamily] = []
    for key, members in groups.items():
        # Stable family id derived from the key
        fid = "fam:DOCDB:" + hashlib.sha256(key.encode()).hexdigest()[:12]
        all_jurisdictions = set()
        earliest = None
        for m in members:
            # mutate the in-memory patent to carry the canonical family id
            object.__setattr__(m, "docdb_family_id", fid)
            all_jurisdictions.update(m.jurisdictions)
            pd = m.priority_date
            if pd and (earliest is None or pd < earliest):
                earliest = pd
        families.append(PatentFamily(
            family_id=fid,
            member_patent_ids=[m.patent_id for m in members],
            earliest_priority_date=earliest,
            jurisdictions=sorted(all_jurisdictions),
            domain=members[0].domain,
        ))
    return families


def family_id_of(patent: Patent) -> str:
    """Return the canonical family id for a patent (computed or assigned)."""
    if patent.docdb_family_id and patent.docdb_family_id.startswith("fam:DOCDB:"):
        return patent.docdb_family_id
    # Recompute on the fly if missing
    key = _priority_chain_key(patent)
    return "fam:DOCDB:" + hashlib.sha256(key.encode()).hexdigest()[:12]


def jurisdictional_coverage(family: PatentFamily) -> set[str]:
    return set(family.jurisdictions)
