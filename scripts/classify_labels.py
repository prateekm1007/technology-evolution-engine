#!/usr/bin/env python3
"""
Phase 5.E — Classification exercise (per CEO v3.1 directive).

The CEO's challenge: the Phase 5.D interpretation said "the system
has saturated." The narrower, defensible claim is "the system has
saturated under the current ingestion strategy and current matching
assumptions." Those are different.

This script performs the classification exercise the CEO authorized:

  Work package A: Partition the 140 component labels into categories.
  Work package B: Compute maximum_possible_bridges under perfect normalization.
  Work package C: Compute signal_loss = potential / (exact + potential).
  Work package D: Produce a ceiling estimate (current / perfect / upper bound).

Per the CEO's directive:
  'The point of this exercise is not to solve the bottleneck. It is
   to determine whether the bottleneck is large enough to justify
   solving it at all. That distinction is extremely important.'

This is a MEASUREMENT script. It does NOT modify the parser, formula,
ontology, or governance rules. It does NOT ingest additional papers.
"""
import json
import pathlib
import re
from collections import defaultdict
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "civilization_graph.json"


def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def all_component_labels(graph):
    """Return list of all component-typed labels with their source info."""
    labels = []
    for n in graph["nodes"]:
        if n.get("type") != "component":
            continue
        prov = n.get("provenance", {})
        source = prov.get("patent_number") or prov.get("doi") or prov.get("source", "?")
        labels.append({
            "label": n.get("label", ""),
            "label_key": n.get("label", "").lower().strip(),
            "node_id": n["id"],
            "source": source,
            "domain": prov.get("domain", "?"),
        })
    return labels


# --- Work package A: Classification ---

def classify_labels(labels):
    """Partition labels into 6 categories per CEO directive.

    Categories:
      1. Exact matches: labels shared by 2+ sources (already merged)
      2. Abbreviations: labels that are abbreviations of other labels
      3. Singular/plural variants: labels differing only by pluralization
      4. Hypernyms: labels that are general/specific versions of others
      5. Compound labels: long labels containing simpler labels as substrings
      6. Truly unique labels: none of the above

    A label can only be in ONE category (priority order: 1 > 2 > 3 > 4 > 5 > 6).
    """
    by_key = defaultdict(list)
    for l in labels:
        by_key[l["label_key"]].append(l)

    label_keys = sorted(by_key.keys())
    classified = {
        "exact_matches": [],
        "abbreviations": [],
        "singular_plural": [],
        "hypernyms": [],
        "compound": [],
        "truly_unique": [],
    }
    assigned = set()

    # --- Category 1: Exact matches (labels shared by 2+ sources) ---
    for key in label_keys:
        occs = by_key[key]
        sources = set(l["source"] for l in occs)
        if len(sources) >= 2:
            classified["exact_matches"].append({
                "label": key,
                "count": len(occs),
                "sources": sorted(sources),
            })
            assigned.add(key)

    # --- Category 2: Abbreviations ---
    # Known abbreviation pairs (from NORMALIZATION_GAP.md analysis)
    abbreviation_pairs = [
        ("metal-organic framework", "mof"),
        ("metal-organic framework", "mofs"),
        ("direct air capture", "dac"),
        ("heat exchanger", "hx"),
        ("battery management system", "bms"),
        ("maximum power point tracking", "mppt"),
    ]
    for full, abbr in abbreviation_pairs:
        if full in by_key and abbr in by_key and full not in assigned and abbr not in assigned:
            classified["abbreviations"].append({
                "full": full,
                "abbreviation": abbr,
                "full_sources": sorted(set(l["source"] for l in by_key[full])),
                "abbr_sources": sorted(set(l["source"] for l in by_key[abbr])),
            })
            assigned.add(full)
            assigned.add(abbr)
        elif abbr in by_key and abbr not in assigned:
            # Abbreviation present but full form not extracted (extraction gap)
            classified["abbreviations"].append({
                "full": f"(not in graph — extraction gap) {full}",
                "abbreviation": abbr,
                "full_sources": [],
                "abbr_sources": sorted(set(l["source"] for l in by_key[abbr])),
            })
            assigned.add(abbr)
        elif full in by_key and full not in assigned:
            # Full form present but abbreviation not extracted
            classified["abbreviations"].append({
                "full": full,
                "abbreviation": f"(not in graph — extraction gap) {abbr}",
                "full_sources": sorted(set(l["source"] for l in by_key[full])),
                "abbr_sources": [],
            })
            assigned.add(full)

    # --- Category 3: Singular/plural variants ---
    # Check if "X" and "Xs" both appear as labels
    for key in label_keys:
        if key in assigned:
            continue
        plural = key + "s"
        if plural in by_key and plural not in assigned:
            classified["singular_plural"].append({
                "singular": key,
                "plural": plural,
                "singular_sources": sorted(set(l["source"] for l in by_key[key])),
                "plural_sources": sorted(set(l["source"] for l in by_key[plural])),
            })
            assigned.add(key)
            assigned.add(plural)
        # Also check "X" and "Xes" (e.g., box/boxes)
        plural_es = key + "es"
        if plural_es in by_key and plural_es not in assigned:
            classified["singular_plural"].append({
                "singular": key,
                "plural": plural_es,
                "singular_sources": sorted(set(l["source"] for l in by_key[key])),
                "plural_sources": sorted(set(l["source"] for l in by_key[plural_es])),
            })
            assigned.add(key)
            assigned.add(plural_es)

    # --- Category 4: Hypernyms (general/specific) ---
    # Known hypernym pairs from the analysis
    hypernym_pairs = [
        ("electrode", "anode"),
        ("electrode", "cathode"),
        ("sorbent", "adsorbent"),  # near-synonym, treated as hypernym for classification
        ("sensor", "thermometer"),
        ("sensor", "hygrometer"),
        ("actuator", "motor"),
        ("actuator", "valve"),
        ("filter", "membrane"),
    ]
    for hyper, hypo in hypernym_pairs:
        if hyper in by_key and hypo in by_key and hyper not in assigned and hypo not in assigned:
            classified["hypernyms"].append({
                "hypernym": hyper,
                "hyponym": hypo,
                "hyper_sources": sorted(set(l["source"] for l in by_key[hyper])),
                "hypo_sources": sorted(set(l["source"] for l in by_key[hypo])),
            })
            assigned.add(hyper)
            assigned.add(hypo)

    # --- Category 5: Compound labels (long labels containing simpler labels) ---
    # A label is "compound" if it's >20 chars AND contains a shorter label
    # as a WORD (not just a substring — word-boundary matching avoids false
    # positives like "imu" matching inside "maximum").
    short_labels = [k for k in label_keys if len(k) <= 20 and k not in assigned]
    for key in label_keys:
        if key in assigned or len(key) <= 20:
            continue
        # Check if this long label contains any short label as a WORD
        # (word-boundary match, not substring).
        contained = []
        for short in short_labels:
            if short != key and re.search(r'\b' + re.escape(short) + r'\b', key):
                contained.append(short)
        if contained:
            classified["compound"].append({
                "compound_label": key[:80] + ("..." if len(key) > 80 else ""),
                "contains": contained,
                "sources": sorted(set(l["source"] for l in by_key[key])),
            })
            assigned.add(key)

    # --- Category 6: Truly unique labels ---
    for key in label_keys:
        if key not in assigned:
            occs = by_key[key]
            classified["truly_unique"].append({
                "label": key[:80] + ("..." if len(key) > 80 else ""),
                "count": len(occs),
                "sources": sorted(set(l["source"] for l in occs)),
            })

    return classified


# --- Work package B: maximum_possible_bridges ---

def compute_max_bridges(classified):
    """Under perfect normalization, how many bridges could exist?

    A bridge = a pair of labels that COULD share a node under some
    normalization rule. This is the theoretical maximum if every
    normalization gap were resolved.

    Counting:
      - Exact matches already shared: count as 1 bridge each (already realized)
      - Abbreviations: each abbreviation pair = 1 potential bridge
      - Singular/plural: each pair = 1 potential bridge
      - Hypernyms: each hypernym pair = 1 potential bridge
      - Compound labels: each compound containing N shorter labels = N potential bridges
      - Truly unique: 0 bridges (by definition)
    """
    bridges = {
        "exact_realized": len(classified["exact_matches"]),
        "abbreviation_potential": len(classified["abbreviations"]),
        "singular_plural_potential": len(classified["singular_plural"]),
        "hypernym_potential": len(classified["hypernyms"]),
        "compound_potential": sum(len(c["contains"]) for c in classified["compound"]),
    }
    bridges["maximum_possible"] = (
        bridges["exact_realized"]
        + bridges["abbreviation_potential"]
        + bridges["singular_plural_potential"]
        + bridges["hypernym_potential"]
        + bridges["compound_potential"]
    )
    return bridges


# --- Work package C: signal_loss ---

def compute_signal_loss(classified):
    """signal_loss = potential_matches / (exact_matches + potential_matches)

    Per CEO directive. Measures what fraction of the (exact + potential)
    signal is currently being lost to normalization gaps.
    """
    exact = len(classified["exact_matches"])
    potential = (
        len(classified["abbreviations"])
        + len(classified["singular_plural"])
        + len(classified["hypernyms"])
        + sum(len(c["contains"]) for c in classified["compound"])
    )
    if exact + potential == 0:
        return {"exact": exact, "potential": potential, "signal_loss": 0.0}
    return {
        "exact": exact,
        "potential": potential,
        "signal_loss": round(potential / (exact + potential), 4),
    }


# --- Work package D: ceiling estimate ---

def compute_ceiling_estimate(graph, classified):
    """Estimate the convergence score under:
      1. Current state (already measured: 1.2182 for battery×EV)
      2. Perfect normalization (all potential bridges resolved)
      3. Upper bound (theoretical max if all 140 labels collapsed to 1 shared)

    For the perfect-normalization estimate, we simulate what would
    happen if every potential match were merged into a single shared
    node. This is an ANALYTICAL computation, not an implementation.
    """
    # Current battery×EV score (from snapshot_4)
    current_score = 1.2182

    # For perfect normalization: count how many NEW shared components
    # would be created if all potential matches resolved.
    # Each abbreviation pair -> +1 shared node (the full form, with the
    #   abbreviation merged in)
    # Each singular/plural pair -> +1 shared node (the singular, with
    #   the plural merged in)
    # Each hypernym pair -> +1 shared node (the hypernym, with the
    #   hyponym merged in as a subtype — debatable, but for ceiling
    #   estimate we count it)
    # Each compound containing N shorter labels -> +N shared nodes
    #   (the compound merges into each of its shorter labels)
    new_shared_from_abbrev = len(classified["abbreviations"])
    new_shared_from_plural = len(classified["singular_plural"])
    new_shared_from_hyper = len(classified["hypernyms"])
    new_shared_from_compound = sum(len(c["contains"]) for c in classified["compound"])

    # Current shared_components for battery×EV is 1.
    # Perfect normalization would add the new shared components that
    # fall WITHIN the battery×EV subtrees. Not all potential matches
    # are relevant to battery×EV — some are in other domains.
    # For a ceiling estimate, assume ALL potential matches are relevant.
    new_shared_total = (
        new_shared_from_abbrev
        + new_shared_from_plural
        + new_shared_from_hyper
        + new_shared_from_compound
    )

    # Current: shared=1, total=11 (battery subtree=7, EV subtree=5, overlap=1)
    # Perfect: shared = 1 + new_shared_total, total stays ~11 (we're
    #   merging existing nodes, not adding new ones — the total
    #   component count actually DECREASES because we're collapsing
    #   duplicates)
    # For a conservative ceiling: assume total stays at 11 (no decrease).
    perfect_shared = 1 + new_shared_total
    perfect_total = 11  # conservative: total unchanged
    perfect_overlap = perfect_shared / perfect_total if perfect_total else 0
    perfect_score = 1.0 + 0.4 * 0 + 0.2 * perfect_overlap + 0.2 * 1.0  # direct_dep + prereq + path

    # Upper bound: theoretical maximum if Signal C overlap = 1.0
    # (all components shared). This would require total collapse.
    upper_bound_score = 1.0 + 0.4 * 0 + 0.2 * 1.0 + 0.2 * 1.0  # = 1.4

    return {
        "current_score": current_score,
        "perfect_normalization_shared": perfect_shared,
        "perfect_normalization_total": perfect_total,
        "perfect_normalization_overlap": round(perfect_overlap, 4),
        "perfect_normalization_score": round(perfect_score, 4),
        "upper_bound_score": upper_bound_score,
        "upper_bound_assumption": "all components shared (overlap_ratio = 1.0)",
    }


def main():
    print("=" * 70)
    print("PHASE 5.E — CLASSIFICATION EXERCISE (per CEO v3.1 directive)")
    print("=" * 70)

    graph = load_graph()
    labels = all_component_labels(graph)
    print(f"\nTotal component labels: {len(labels)}")
    by_key = defaultdict(list)
    for l in labels:
        by_key[l["label_key"]].append(l)
    print(f"Distinct labels: {len(by_key)}")

    # --- Work package A ---
    print(f"\n--- Work package A: Classification ---")
    classified = classify_labels(labels)
    total_classified = sum(len(v) for v in classified.values())
    print(f"\n{'Category':<30} {'Count':>6}")
    print("-" * 40)
    for cat, items in classified.items():
        print(f"  {cat:<28} {len(items):>6}")
    print(f"  {'TOTAL':<28} {total_classified:>6}")

    print(f"\nExact matches (labels shared by 2+ sources):")
    for em in classified["exact_matches"][:15]:
        print(f"  - {em['label']!r}: {em['count']} sources")
    print(f"\nAbbreviations:")
    for ab in classified["abbreviations"]:
        print(f"  - {ab['full']!r} <-> {ab['abbreviation']!r}")
    print(f"\nSingular/plural variants:")
    for sp in classified["singular_plural"]:
        print(f"  - {sp['singular']!r} <-> {sp['plural']!r}")
    print(f"\nHypernyms:")
    for h in classified["hypernyms"]:
        print(f"  - {h['hypernym']!r} <-> {h['hyponym']!r}")
    print(f"\nCompound labels (first 5):")
    for c in classified["compound"][:5]:
        print(f"  - {c['compound_label']!r} contains {c['contains']}")
    print(f"  ... ({len(classified['compound'])} total compound labels)")
    print(f"\nTruly unique labels (first 10):")
    for u in classified["truly_unique"][:10]:
        print(f"  - {u['label']!r}")
    print(f"  ... ({len(classified['truly_unique'])} total truly unique)")

    # --- Work package B ---
    print(f"\n--- Work package B: maximum_possible_bridges ---")
    bridges = compute_max_bridges(classified)
    print(f"\n{'Bridge type':<35} {'Count':>6}")
    print("-" * 45)
    for bt, count in bridges.items():
        print(f"  {bt:<33} {count:>6}")

    # --- Work package C ---
    print(f"\n--- Work package C: signal_loss ---")
    sl = compute_signal_loss(classified)
    print(f"\n  exact_matches:    {sl['exact']}")
    print(f"  potential_matches: {sl['potential']}")
    print(f"  signal_loss = potential / (exact + potential) = {sl['signal_loss']}")
    print(f"  (i.e., {sl['signal_loss']*100:.1f}% of the bridgeable signal is currently lost)")

    # --- Work package D ---
    print(f"\n--- Work package D: ceiling estimate ---")
    ceiling = compute_ceiling_estimate(graph, classified)
    print(f"\n  {'State':<30} {'Score':>8}")
    print(f"  {'-'*40}")
    print(f"  {'Current':<30} {ceiling['current_score']:>8.4f}")
    print(f"  {'Perfect normalization':<30} {ceiling['perfect_normalization_score']:>8.4f}")
    print(f"  {'Upper bound (all shared)':<30} {ceiling['upper_bound_score']:>8.4f}")
    print(f"\n  Perfect normalization assumes:")
    print(f"    shared_components: 1 -> {ceiling['perfect_normalization_shared']}")
    print(f"    total_components: 11 (unchanged — conservative)")
    print(f"    overlap_ratio: {ceiling['perfect_normalization_overlap']}")
    print(f"\n  Upper bound assumes:")
    print(f"    overlap_ratio = 1.0 (all components shared)")


if __name__ == "__main__":
    main()
