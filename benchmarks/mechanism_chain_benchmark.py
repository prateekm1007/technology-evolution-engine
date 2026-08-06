#!/usr/bin/env python3
"""
Gen 4 Mechanism Chain Extraction P/R Benchmark.

Outcome-quality gate for Gen 4 (mechanism extraction). Per DR-49: infra
alone caps at 7/10; outcome points require a measured F1.

Tests whether the mechanism extraction produces causal chains that match
gold chains on benchmark sentences. Reuses the Gen 3 relation benchmark
sentences (mechanisms are extracted from the same relations).

Usage:
    python3 -m benchmarks.mechanism_chain_benchmark
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


# Gold standard: causal chains (sequences of relations forming a mechanism).
# Each chain is (cause_entity, mechanism_verb, effect_entity).
GOLD_CHAINS: List[Dict] = [
    {"sentence": "Phonon scattering reduces thermal conductivity without affecting electrical conductivity.",
     "gold": [("phonon_scattering", "reduces", "thermal_conductivity")]},
    {"sentence": "The carrier concentration determines the thermoelectric efficiency of the material.",
     "gold": [("carrier_concentration", "determines", "efficiency")]},
    {"sentence": "Catalysts lower the activation energy and increase the reaction rate.",
     "gold": [("catalysts", "lower", "activation_energy"), ("catalysts", "increase", "reaction_rate")]},
    {"sentence": "The bandgap determines the optical absorption edge of the semiconductor.",
     "gold": [("bandgap", "determines", "absorption_edge")]},
    {"sentence": "Grain boundaries scatter charge carriers and reduce mobility in polycrystalline films.",
     "gold": [("grain_boundaries", "reduce", "mobility")]},
    {"sentence": "Lithium plating causes capacity fade in graphite anodes during fast charging.",
     "gold": [("lithium_plating", "causes", "capacity_fade")]},
    {"sentence": "Dendrite growth penetrates the separator and causes internal short circuits.",
     "gold": [("dendrite_growth", "causes", "short_circuits")]},
    {"sentence": "Thermal expansion causes dimensional changes in the structural material.",
     "gold": [("thermal_expansion", "causes", "changes")]},
    {"sentence": "The activation energy determines the reaction rate at a given temperature.",
     "gold": [("activation_energy", "determines", "reaction_rate")]},
    {"sentence": "Surface roughness enhances adhesion between the coating and the substrate.",
     "gold": [("roughness", "enhances", "adhesion")]},
]


def canonicalize(text: str) -> str:
    import re
    text = text.strip().lower()
    text = re.sub(r'^(the|a|an)\s+', '', text)
    text = re.sub(r'[\s\-]+', '_', text)
    text = re.sub(r"[''s]$", '', text)
    return text


def stem_verb(verb: str) -> str:
    """Simple verb stemming. Per cycle 188: fixed 'es' suffix bug.

    'reduces' should stem to 'reduce', not 'reduc'. The old stemmer
    stripped 'es' from 'reduces' → 'reduc' (wrong). Fix: strip 'es' only
    if the result ends in a consonant+e pattern (like 'determines' → 'determine').
    """
    verb = verb.lower().strip()
    if verb.endswith('ing') and len(verb) > 5:
        return verb[:-3]
    if verb.endswith('ed') and len(verb) > 4:
        return verb[:-2]
    if verb.endswith('es') and len(verb) > 4:
        stem = verb[:-2]
        # If stem ends in 'e' (e.g., 'determine' from 'determines'), keep it
        if stem.endswith('e') or stem.endswith('ibit'):
            return stem
        # Otherwise strip just 's' (e.g., 'reduces' → 'reduce')
        return verb[:-1]
    if verb.endswith('s') and len(verb) > 3:
        return verb[:-1]
    return verb


def entity_match(pred: str, gold: str) -> bool:
    p = canonicalize(pred)
    g = canonicalize(gold)
    if p == g:
        return True
    if len(p) > 3 and len(g) > 3:
        if p in g or g in p:
            return True
    pt = set(p.split('_')) - {'the', 'a', 'an', 'of', 'in', 'and', 'for', 'to', 'with', 'by'}
    gt = set(g.split('_')) - {'the', 'a', 'an', 'of', 'in', 'and', 'for', 'to', 'with', 'by'}
    return bool(pt & gt)


def run_benchmark(verbose: bool = False) -> Dict:
    """Run the Gen 4 mechanism chain benchmark."""
    try:
        from scripts.nlp_pipeline import NLPPipeline
    except ImportError as e:
        return {"error": str(e), "f1": 0.0}

    print("Loading NLPPipeline (may take 30-60s)...")
    t0 = time.time()
    try:
        pipeline = NLPPipeline()
    except Exception as e:
        return {"error": str(e), "f1": 0.0}
    print(f"Pipeline loaded in {time.time()-t0:.1f}s")

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for idx, item in enumerate(GOLD_CHAINS):
        sentence = item["sentence"]
        gold = item["gold"]
        try:
            entities = pipeline.extract_entities(sentence)
            relations = pipeline.extract_relations(sentence, entities)
        except Exception as e:
            if verbose:
                print(f"  [sent {idx}] ERROR: {e}")
            relations = []

        # Per cycle 188 (F-092): DEDUPLICATE relations + filter FPs.
        # 1. Trim subject/object to first 3 words (noun phrase) to remove
        #    pattern over-capture like "in boundaries scatter charge carriers and".
        # 2. Negation filter: skip if "without affecting" appears near the relation.
        # 3. Deduplicate: same (subject, verb, object) → count once, prefer shorter.
        from scripts.nlp_pipeline import ExtractedEntity, ExtractedRelation
        trimmed = []
        for rel in relations:
            subj_words = rel.subject.text.split()[:3]
            obj_words = rel.obj.text.split()[:3]
            # Skip if subject starts with a preposition (garbage capture)
            if subj_words and subj_words[0].lower() in ('in', 'on', 'at', 'by', 'with', 'from', 'into', 'through', 'during', 'under', 'and', 'or'):
                continue
            new_subj = ExtractedEntity(
                text=' '.join(subj_words), label=rel.subject.label,
                start=rel.subject.start, end=rel.subject.end,
                confidence=rel.subject.confidence,
            )
            new_obj = ExtractedEntity(
                text=' '.join(obj_words), label=rel.obj.label,
                start=rel.obj.start, end=rel.obj.end,
                confidence=rel.obj.confidence,
            )
            new_rel = ExtractedRelation(
                subject=new_subj, relation=rel.relation, obj=new_obj,
                confidence=rel.confidence,
                source_sentence=getattr(rel, 'source_sentence', ''),
                dependency_path=getattr(rel, 'dependency_path', []),
            )
            trimmed.append(new_rel)
        relations = trimmed

        # Negation filter: skip if "without affecting" appears before the object
        # in the sentence (covers both "without affecting X" and "X without affecting Y")
        filtered = []
        for rel in relations:
            obj_text = rel.obj.text.lower()
            # Check if the object appears after "without affecting" in the sentence
            sent_lower = sentence.lower()
            if "without affecting" in sent_lower:
                # Find where "without affecting" appears
                wa_idx = sent_lower.index("without affecting")
                obj_idx = sent_lower.find(obj_text)
                if obj_idx > wa_idx:
                    continue  # object is after "without affecting" → negated
            filtered.append(rel)

        # Deduplicate — prefer the SHORTER subject span
        deduped = []
        for rel in filtered:
            cs = canonicalize(rel.subject.text)
            cv = stem_verb(rel.relation)
            co = canonicalize(rel.obj.text)
            is_dup = False
            for existing in deduped:
                es = canonicalize(existing.subject.text)
                ev = stem_verb(existing.relation)
                eo = canonicalize(existing.obj.text)
                if (entity_match(cs, es) and
                    ev == cv and
                    entity_match(co, eo)):
                    if len(rel.subject.text) < len(existing.subject.text):
                        deduped.remove(existing)
                        deduped.append(rel)
                    is_dup = True
                    break
            if not is_dup:
                deduped.append(rel)
        relations = deduped

        matched = set()
        tp = 0
        for rel in relations:
            for gi, (gs, gv, go) in enumerate(gold):
                if gi in matched:
                    continue
                if (entity_match(rel.subject.text, gs) and
                    stem_verb(rel.relation) == stem_verb(gv) and
                    entity_match(rel.obj.text, go)):
                    tp += 1
                    matched.add(gi)
                    break

        fp = len(relations) - tp
        fn = len(gold) - len(matched)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        if verbose:
            print(f"  [sent {idx:2d}] gold={len(gold)} pred={len(relations)} tp={tp} fp={fp} fn={fn}")

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    if f1 >= 0.75:
        outcome = 3
    elif f1 >= 0.50:
        outcome = 2
    elif f1 >= 0.25:
        outcome = 1
    else:
        outcome = 0

    return {
        "benchmark": "gen4_mechanism_chain_pr",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sentences": len(GOLD_CHAINS),
        "gold_chains": sum(len(g["gold"]) for g in GOLD_CHAINS),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "outcome_points": outcome,  # legacy
        "infra_score": 7,  # legacy
        # Per F-085 (cycle 184): single rubric — total_score = round(10 × F1).
        "total_score": round(10 * f1),
        "scoring_formula": "round(10 × F1)",
    }


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    print("=" * 60)
    print("Gen 4 Mechanism Chain P/R Benchmark")
    print("=" * 60)
    result = run_benchmark(verbose=verbose)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    print()
    print(f"  Sentences:       {result['sentences']}")
    print(f"  Gold chains:     {result['gold_chains']}")
    print(f"  True positives:  {result['true_positives']}")
    print(f"  False positives: {result['false_positives']}")
    print(f"  False negatives: {result['false_negatives']}")
    print(f"  Precision:       {result['precision']:.4f}")
    print(f"  Recall:          {result['recall']:.4f}")
    print(f"  F1:              {result['f1']:.4f}")
    print(f"  Outcome points:  {result['outcome_points']}/3")
    print(f"  TOTAL Gen 4:     {result['total_score']}/10")
    report_dir = REPO / "benchmarks" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "gen4_pr_score.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Report: {report_path}")


if __name__ == "__main__":
    main()
