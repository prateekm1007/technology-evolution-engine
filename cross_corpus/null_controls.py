"""
Null controls for the cross-corpus pilot (Issue #4).

Four nulls. Each null must NOT produce a higher confirmation rate than the
real cross-corpus run. If any null beats the real run, the discovery claim
collapses (the cross-corpus signal is spurious).

NULL_A — temporal shuffle:
    Shuffle the dates of all documents uniformly. Breaks the time-ordering
    that motifs rely on. If motifs still fire at the same rate, the motifs
    are detecting trivial structural patterns, not temporal discoveries.

NULL_B — corpus-label swap:
    Swap paper/patent labels on 50% of cross-corpus edges. Breaks the
    provenance semantics. If motifs still fire, they are insensitive to
    whether a citation is paper-to-patent vs patent-to-paper — i.e.,
    insensitive to the cross-corpus distinction itself.

NULL_C — degree-matched random graph:
    Replace the citation edges with a random graph having the same degree
    distribution. Breaks the citation semantics. If motifs still fire, they
    are detecting degree-driven artifacts, not citation-driven discoveries.

NULL_D — single-corpus-only:
    Run the motifs on the paper-only subgraph and the patent-only subgraph
    separately (no cross-corpus edges). If the cross-corpus run does not
    exceed the max of these two, cross-corpus adds no value.
"""
from __future__ import annotations
import random
from copy import deepcopy
from .schema import Paper, Patent, PatentFamily, Citation
from .graph import EvidenceGraph
from .family_normalizer import normalize_families


def _shuffle_dates(papers: list[Paper], patents: list[Patent], rng: random.Random):
    """NULL_A helper: uniformly shuffle dates within each corpus."""
    paper_dates = [p.publication_date for p in papers]
    rng.shuffle(paper_dates)
    for p, d in zip(papers, paper_dates):
        object.__setattr__(p, "publication_date", d)
    patent_dates = [p.priority_date or p.publication_date for p in patents]
    rng.shuffle(patent_dates)
    for p, d in zip(patents, patent_dates):
        object.__setattr__(p, "priority_date", d)
        object.__setattr__(p, "publication_date", d)


def build_null_a(papers: list[Paper], patents: list[Patent],
                  seed: int = 42) -> EvidenceGraph:
    """Temporal-shuffle null."""
    rng = random.Random(seed)
    papers_copy = deepcopy(papers)
    patents_copy = deepcopy(patents)
    _shuffle_dates(papers_copy, patents_copy, rng)
    g = EvidenceGraph()
    for p in papers_copy:
        g.add_paper(p)
    for p in patents_copy:
        g.add_patent(p)
    for fam in normalize_families(patents_copy):
        g.add_family(fam)
    return g


def build_null_b(papers: list[Paper], patents: list[Patent],
                  seed: int = 42) -> EvidenceGraph:
    """Corpus-label-swap null: swap paper/patent labels on 50% of cross edges."""
    rng = random.Random(seed)
    papers_copy = deepcopy(papers)
    patents_copy = deepcopy(patents)
    for p in patents_copy:
        new_cits = []
        for c in p.citations:
            if c.target_kind in ("paper", "npl") and rng.random() < 0.5:
                # swap: pretend the cited paper is actually a patent
                new_cits.append(Citation(
                    source_id=c.source_id,
                    target_id=c.target_id.replace("paper:", "patent:", 1)
                                if c.target_id.startswith("paper:") else c.target_id,
                    source_kind="patent",
                    target_kind="patent",
                    role=c.role,
                    citation_date=c.citation_date,
                ))
            else:
                new_cits.append(c)
        object.__setattr__(p, "citations", new_cits)
    g = EvidenceGraph()
    for p in papers_copy:
        g.add_paper(p)
    for p in patents_copy:
        g.add_patent(p)
    for fam in normalize_families(patents_copy):
        g.add_family(fam)
    return g


def build_null_c(papers: list[Paper], patents: list[Patent],
                  seed: int = 42) -> EvidenceGraph:
    """Degree-matched random graph: replace citation edges with random ones.

    We preserve the in-degree and out-degree sequence of citation edges but
    rewire targets randomly. This breaks citation semantics while preserving
    the graph's degree profile (so motif counts that depend only on degree
    are unchanged).
    """
    rng = random.Random(seed)
    papers_copy = deepcopy(papers)
    patents_copy = deepcopy(patents)
    # Collect all citation targets (pool)
    all_targets = []
    for p in papers_copy:
        for c in p.citations:
            all_targets.append(c.target_id)
    for p in patents_copy:
        for c in p.citations:
            all_targets.append(c.target_id)
    if not all_targets:
        # nothing to shuffle
        pass
    else:
        rng.shuffle(all_targets)
        idx = 0
        for p in papers_copy:
            new_cits = []
            for c in p.citations:
                new_target = all_targets[idx % len(all_targets)]
                idx += 1
                new_cits.append(Citation(
                    source_id=c.source_id,
                    target_id=new_target,
                    source_kind=c.source_kind,
                    target_kind=c.target_kind,
                    role=c.role,
                    citation_date=c.citation_date,
                ))
            object.__setattr__(p, "citations", new_cits)
        for p in patents_copy:
            new_cits = []
            for c in p.citations:
                new_target = all_targets[idx % len(all_targets)]
                idx += 1
                new_cits.append(Citation(
                    source_id=c.source_id,
                    target_id=new_target,
                    source_kind=c.source_kind,
                    target_kind=c.target_kind,
                    role=c.role,
                    citation_date=c.citation_date,
                ))
            object.__setattr__(p, "citations", new_cits)
    g = EvidenceGraph()
    for p in papers_copy:
        g.add_paper(p)
    for p in patents_copy:
        g.add_patent(p)
    for fam in normalize_families(patents_copy):
        g.add_family(fam)
    return g


def build_null_d(papers: list[Paper], patents: list[Patent]) -> dict:
    """Single-corpus-only null: run motifs separately on each corpus.

    Returns two subgraphs: {'papers_only': EvidenceGraph, 'patents_only': EvidenceGraph}.
    The orchestrator runs all motifs on each and reports the max candidate count.
    """
    pg = EvidenceGraph()
    for p in papers:
        pg.add_paper(p)
    # paper-only: drop all patent citations, keep paper-paper citations
    pp = EvidenceGraph()
    for p in papers:
        p_copy = deepcopy(p)
        new_cits = [c for c in p_copy.citations if c.target_kind == "paper"]
        object.__setattr__(p_copy, "citations", new_cits)
        pp.add_paper(p_copy)
    # patent-only: keep only patent-patent citations
    po = EvidenceGraph()
    for p in patents:
        p_copy = deepcopy(p)
        new_cits = [c for c in p_copy.citations if c.target_kind == "patent"]
        object.__setattr__(p_copy, "citations", new_cits)
        po.add_patent(p_copy)
    for fam in normalize_families(patents):
        # only add families with members that survived
        surviving_members = [m for m in fam.member_patent_ids if m in po.patents]
        if surviving_members:
            po.add_family(PatentFamily(
                family_id=fam.family_id,
                member_patent_ids=surviving_members,
                earliest_priority_date=fam.earliest_priority_date,
                jurisdictions=fam.jurisdictions,
                domain=fam.domain,
            ))
    return {"papers_only": pp, "patents_only": po}
