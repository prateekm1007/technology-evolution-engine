"""
EvidenceGraph — the unified paper+patent+family graph (Issue #4).

Nodes:
  - paper:<id>
  - patent:<id>
  - fam:<id>          (DOCDB family)
  - material:<token>
  - mechanism:<token>
  - process:<token>
  - domain:<token>

Edges (all provenance-qualified):
  - cites (with EPO role X/Y/A/T/D/*)
  - claims (subject --predicate--> object, with optional negation/value)
  - uses_material / uses_mechanism / uses_process
  - reports_failure
  - family_member_of
  - domain_of

Time-anchored subgraph extraction: given a cutoff date, return the subgraph
containing only nodes whose publication/priority date is strictly before the
cutoff. This is the *evidence available at freeze time* — predictions can only
rely on this subgraph.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime
from typing import Optional
from .schema import Paper, Patent, PatentFamily, Citation, Claim
from .family_normalizer import family_id_of


class EvidenceGraph:
    def __init__(self):
        self.papers: dict[str, Paper] = {}
        self.patents: dict[str, Patent] = {}
        self.families: dict[str, PatentFamily] = {}
        # adjacency: node_id -> list of (edge_type, target_id, payload)
        self.adj: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)
        # reverse adjacency for backward traversal
        self.radj: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)

    # --- ingestion ---
    def add_paper(self, p: Paper):
        if p.paper_id in self.papers:
            raise ValueError(f"Duplicate paper: {p.paper_id}")
        self.papers[p.paper_id] = p
        nid = p.node_id()
        for c in p.citations:
            self._add_edge(nid, c.target_id, "cites",
                           {"role": c.role, "target_kind": c.target_kind})
        for m in p.materials:
            self._add_edge(nid, f"material:{m}", "uses_material", {})
        for m in p.mechanisms:
            self._add_edge(nid, f"mechanism:{m}", "uses_mechanism", {})
        for pr in p.processes:
            if isinstance(pr, str) and pr.startswith("PRIORITY_CHAIN:"):
                continue  # not a real process edge
            self._add_edge(nid, f"process:{pr}", "uses_process", {})
        for f in p.reported_failures:
            self._add_edge(nid, f"failure:{hash(f)}", "reports_failure",
                           {"text": f})
        for cl in p.claims:
            self._add_claim_edge(nid, cl)
        self._add_edge(nid, f"domain:{p.domain}", "domain_of", {})

    def add_patent(self, p: Patent):
        if p.patent_id in self.patents:
            raise ValueError(f"Duplicate patent: {p.patent_id}")
        self.patents[p.patent_id] = p
        nid = p.node_id()
        for c in p.citations:
            self._add_edge(nid, c.target_id, "cites",
                           {"role": c.role, "target_kind": c.target_kind})
        for m in p.materials:
            self._add_edge(nid, f"material:{m}", "uses_material", {})
        for m in p.mechanisms:
            self._add_edge(nid, f"mechanism:{m}", "uses_mechanism", {})
        for pr in p.processes:
            if isinstance(pr, str) and pr.startswith("PRIORITY_CHAIN:"):
                continue
            self._add_edge(nid, f"process:{pr}", "uses_process", {})
        for cl in p.claims:
            self._add_claim_edge(nid, cl)
        self._add_edge(nid, f"domain:{p.domain}", "domain_of", {})

    def add_family(self, f: PatentFamily):
        if f.family_id in self.families:
            raise ValueError(f"Duplicate family: {f.family_id}")
        self.families[f.family_id] = f
        for pid in f.member_patent_ids:
            self._add_edge(pid, f.family_id, "family_member_of", {})

    def _add_edge(self, src: str, dst: str, etype: str, payload: dict):
        self.adj[src].append((etype, dst, payload))
        self.radj[dst].append((etype, src, payload))

    def _add_claim_edge(self, src: str, cl: Claim):
        # claim edge: src --predicate(-> obj) with negation/value
        self._add_edge(src, cl.obj, "claim",
                       {"predicate": cl.predicate, "negated": cl.negated,
                        "value": cl.value, "subject": cl.subject})

    # --- queries ---
    def neighbors(self, nid: str, etype: Optional[str] = None):
        for e, dst, pl in self.adj.get(nid, []):
            if etype is None or e == etype:
                yield e, dst, pl

    def reverse_neighbors(self, nid: str, etype: Optional[str] = None):
        for e, src, pl in self.radj.get(nid, []):
            if etype is None or e == etype:
                yield e, src, pl

    def get_node_date(self, nid: str) -> Optional[str]:
        if nid.startswith("paper:"):
            p = self.papers.get(nid)
            return p.publication_date if p else None
        if nid.startswith("patent:"):
            p = self.patents.get(nid)
            return p.priority_date or p.publication_date if p else None
        if nid.startswith("fam:"):
            f = self.families.get(nid)
            return f.earliest_priority_date if f else None
        return None

    def node_kind(self, nid: str) -> str:
        if nid.startswith("paper:"):
            return "paper"
        if nid.startswith("patent:"):
            return "patent"
        if nid.startswith("fam:"):
            return "family"
        if nid.startswith("material:"):
            return "material"
        if nid.startswith("mechanism:"):
            return "mechanism"
        if nid.startswith("process:"):
            return "process"
        if nid.startswith("domain:"):
            return "domain"
        if nid.startswith("failure:"):
            return "failure"
        return "unknown"

    def time_anchored_subgraph(self, cutoff: str) -> "EvidenceGraph":
        """Return a subgraph containing only nodes dated strictly before cutoff.

        Edges are preserved iff both endpoints survive. Family nodes survive iff
        at least one member survives. Material/mechanism/process/domain/failure
        nodes always survive (they have no date).
        """
        sub = EvidenceGraph()
        cutoff_d = cutoff
        # papers
        for pid, p in self.papers.items():
            if p.publication_date and p.publication_date < cutoff_d:
                sub.add_paper(p)
        # patents
        for pid, p in self.patents.items():
            d = p.priority_date or p.publication_date
            if d and d < cutoff_d:
                sub.add_patent(p)
        # families — re-add families with surviving members
        for fid, fam in self.families.items():
            surviving = [m for m in fam.member_patent_ids if m in sub.patents]
            if surviving:
                from .schema import PatentFamily as PF
                sub.add_family(PF(
                    family_id=fam.family_id,
                    member_patent_ids=surviving,
                    earliest_priority_date=fam.earliest_priority_date,
                    jurisdictions=fam.jurisdictions,
                    domain=fam.domain,
                ))
        return sub

    def cross_corpus_citations(self) -> list[tuple[str, str, str, dict]]:
        """All citation edges crossing the paper/patent boundary.

        Returns (src, dst, role, payload) tuples.
        """
        out = []
        for src, edges in self.adj.items():
            for etype, dst, pl in edges:
                if etype != "cites":
                    continue
                src_kind = self.node_kind(src)
                dst_kind = self.node_kind(dst)
                if dst_kind == "unknown":
                    dst_kind = pl.get("target_kind", "unknown")
                if {src_kind, dst_kind} == {"paper", "patent"} or \
                   (src_kind == "patent" and dst_kind in ("paper",)):
                    out.append((src, dst, pl.get("role", "*"), pl))
        return out

    def stats(self) -> dict:
        n_papers = len(self.papers)
        n_patents = len(self.patents)
        n_families = len(self.families)
        n_edges = sum(len(v) for v in self.adj.values())
        n_cross = len(self.cross_corpus_citations())
        n_claims = sum(1 for src, edges in self.adj.items()
                       for e, _, _ in edges if e == "claim")
        return {
            "papers": n_papers,
            "patents": n_patents,
            "families": n_families,
            "edges": n_edges,
            "cross_corpus_citations": n_cross,
            "claim_edges": n_claims,
        }
