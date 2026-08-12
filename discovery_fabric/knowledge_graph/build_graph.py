"""
Discovery Fabric — Knowledge Graph builder.

Reads evidence.jsonl, builds a knowledge graph connecting:
- papers (evidence items)
- domains
- sources
- authors
- organizations
- citations (where available)
- mechanisms (keyword-extracted)
- classifications (where available)

The graph preserves provenance back to the original evidence.
"""
import json
import sys
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
GRAPH_DIR = REPO / "discovery_fabric/knowledge_graph"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Mechanism keywords for structured extraction
MECHANISM_KEYWORDS = {
    "electrochemical": {"keywords": ["electrochemical", "electrode", "electrolyte", "ion transfer", "redox"], "mechanism": "electrochemical_process"},
    "photovoltaic": {"keywords": ["photovoltaic", "solar cell", "light absorption", "charge generation"], "mechanism": "photovoltaic_conversion"},
    "catalytic": {"keywords": ["catalyst", "catalytic", "active site", "reaction rate"], "mechanism": "catalytic_process"},
    "thermal": {"keywords": ["thermal", "heat transfer", "temperature", "thermodynamic"], "mechanism": "thermal_process"},
    "mechanical": {"keywords": ["mechanical", "stress", "strain", "force", "load"], "mechanism": "mechanical_process"},
    "electromagnetic": {"keywords": ["electromagnetic", "magnetic field", "electric field", "induction"], "mechanism": "electromagnetic_process"},
    "chemical_synthesis": {"keywords": ["synthesis", "chemical reaction", "polymerization", "deposition"], "mechanism": "chemical_synthesis"},
    "additive_manufacturing": {"keywords": ["additive manufacturing", "3d printing", "layer", "deposition"], "mechanism": "additive_manufacturing"},
    "neural_network": {"keywords": ["neural network", "deep learning", "training", "inference"], "mechanism": "neural_computation"},
    "gene_editing": {"keywords": ["crispr", "gene editing", "genetic", "dna"], "mechanism": "genetic_engineering"},
    "surface_modification": {"keywords": ["surface", "interface", "coating", "adhesion"], "mechanism": "surface_modification"},
    "nanostructure": {"keywords": ["nanoparticle", "nanostructure", "nanoscale", "quantum confinement"], "mechanism": "nanostructure_engineering"},
    "polymer": {"keywords": ["polymer", "polymeric", "monomer", "crosslink"], "mechanism": "polymer_engineering"},
    "semiconductor": {"keywords": ["semiconductor", "bandgap", "doping", "carrier"], "mechanism": "semiconductor_process"},
    "biological": {"keywords": ["biological", "biomimetic", "bio-inspired", "enzyme"], "mechanism": "biological_process"},
    "fluid_dynamics": {"keywords": ["fluid", "flow", "viscosity", "turbulence"], "mechanism": "fluid_dynamics"},
    "optical": {"keywords": ["optical", "photon", "waveguide", "refraction"], "mechanism": "optical_process"},
    "acoustic": {"keywords": ["acoustic", "ultrasonic", "sound wave", "vibration"], "mechanism": "acoustic_process"},
}

# Materials keywords
MATERIAL_KEYWORDS = [
    "lithium", "graphene", "silicon", "carbon", "polymer", "ceramic", "metal",
    "perovskite", "titanium", "copper", "aluminum", "steel", "composite",
    "hydrogel", "protein", "dna", "lipid", "cellulose", "chitin",
    "metal-organic framework", "zeolite", "quantum dot", "nanowire",
]

# Process keywords
PROCESS_KEYWORDS = [
    "deposition", "etching", "lithography", "annealing", "sintering",
    "electrospinning", "spin coating", "chemical vapor deposition",
    "atomic layer deposition", "self-assembly", "crystallization",
    "fermentation", "extraction", "purification", "characterization",
]


def extract_mechanisms(text: str) -> list:
    """Extract mechanisms from text using keyword matching."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for mech_id, info in MECHANISM_KEYWORDS.items():
        for kw in info["keywords"]:
            if kw in text_lower:
                found.append(info["mechanism"])
                break
    return list(set(found))


def extract_materials(text: str) -> list:
    """Extract materials from text."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for mat in MATERIAL_KEYWORDS:
        if mat in text_lower:
            found.append(mat)
    return list(set(found))


def extract_processes(text: str) -> list:
    """Extract processes from text."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for proc in PROCESS_KEYWORDS:
        if proc in text_lower:
            found.append(proc)
    return list(set(found))


def build_graph():
    """Build the knowledge graph from evidence."""
    print("Loading evidence...")
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                evidence.append(json.loads(line))
    print(f"  Loaded {len(evidence)} evidence items")

    # Entities
    papers = []
    domains = set()
    sources = set()
    authors = set()
    organizations = set()
    mechanisms = set()
    materials = set()
    processes = set()

    # Edges
    edges = []

    for e in evidence:
        # Paper entity
        papers.append({
            "id": e["id"],
            "title": e.get("title", "")[:150],
            "source": e.get("source", ""),
            "domain": e.get("domain", ""),
            "publication_date": e.get("publication_date", ""),
            "has_abstract": bool(e.get("abstract") and e["abstract"] != "UNAVAILABLE"),
        })

        if e.get("domain"):
            domains.add(e["domain"])
        if e.get("source"):
            sources.add(e["source"])

        # Author edges
        if e.get("authors") and e["authors"] != "UNAVAILABLE":
            for author in e["authors"][:5]:  # limit to first 5
                authors.add(author)
                edges.append({"type": "AUTHORED_BY", "source": e["id"], "target": author})

        # Organization edges
        if e.get("organizations") and e["organizations"] != "UNAVAILABLE":
            for org in e["organizations"][:3]:
                organizations.add(org)
                edges.append({"type": "PUBLISHED_BY", "source": e["id"], "target": org})

        # Mechanism extraction from abstract
        text = ""
        if e.get("abstract") and e["abstract"] != "UNAVAILABLE":
            text = e["abstract"]
        if e.get("title") and e["title"] != "UNAVAILABLE":
            text = text + " " + e["title"]

        found_mechanisms = extract_mechanisms(text)
        for mech in found_mechanisms:
            mechanisms.add(mech)
            edges.append({"type": "USES_MECHANISM", "source": e["id"], "target": mech})

        found_materials = extract_materials(text)
        for mat in found_materials:
            materials.add(mat)
            edges.append({"type": "USES_MATERIAL", "source": e["id"], "target": mat})

        found_processes = extract_processes(text)
        for proc in found_processes:
            processes.add(proc)
            edges.append({"type": "USES_PROCESS", "source": e["id"], "target": proc})

        # Citation edges (where available)
        if e.get("references") and e["references"] != "UNAVAILABLE":
            for ref in e["references"][:10]:  # limit
                edges.append({"type": "CITES", "source": e["id"], "target": ref})

    # Build graph
    graph = {
        "entities": {
            "papers": papers,
            "domains": list(domains),
            "sources": list(sources),
            "authors": list(authors),
            "organizations": list(organizations),
            "mechanisms": list(mechanisms),
            "materials": list(materials),
            "processes": list(processes),
        },
        "edges": edges,
        "stats": {
            "total_papers": len(papers),
            "total_domains": len(domains),
            "total_sources": len(sources),
            "total_authors": len(authors),
            "total_organizations": len(organizations),
            "total_mechanisms": len(mechanisms),
            "total_materials": len(materials),
            "total_processes": len(processes),
            "total_edges": len(edges),
            "edges_by_type": dict(Counter(e["type"] for e in edges)),
        },
    }

    # Save
    output = GRAPH_DIR / "knowledge_graph.json"
    with open(output, "w") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print(f"\nKnowledge Graph built:")
    print(f"  Papers: {graph['stats']['total_papers']}")
    print(f"  Domains: {graph['stats']['total_domains']}")
    print(f"  Sources: {graph['stats']['total_sources']}")
    print(f"  Authors: {graph['stats']['total_authors']}")
    print(f"  Organizations: {graph['stats']['total_organizations']}")
    print(f"  Mechanisms: {graph['stats']['total_mechanisms']}")
    print(f"  Materials: {graph['stats']['total_materials']}")
    print(f"  Processes: {graph['stats']['total_processes']}")
    print(f"  Total edges: {graph['stats']['total_edges']}")
    print(f"  Edges by type: {graph['stats']['edges_by_type']}")
    print(f"  Saved: {output}")

    return graph


if __name__ == "__main__":
    build_graph()
