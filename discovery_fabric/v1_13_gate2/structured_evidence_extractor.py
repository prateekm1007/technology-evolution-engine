"""
V1.13 GATE 2 — Structured Evidence Extractor (DETERMINISTIC, no LLM)
=====================================================================

Converts raw evidence text into a structured evidence object:

    {
      "entities":             [...],   # proper nouns + technical nouns
      "mechanisms":            [...],   # subject-verb-object triples
      "causal_edges":          [...],   # {cause, effect, type: CAUSES|ENABLES|PREVENTS|INHIBITS}
      "combinations":          [...],   # explicit conjunctions (X and Y → Z)
      "constraints":           [...],   # {subject, relation, value}
      "negations":             [...],   # explicit negative statements (X is NOT Y)
      "raw_text":              "...",
      "extraction_method":     "deterministic_regex_v1"
    }

This is NOT a semantic parser. It is a regex-based extractor that catches
surface-form relational statements. It is intentionally conservative:
    - it only extracts what is *explicitly stated* in the evidence
    - it does NOT infer or compose relations
    - it does NOT use any LLM

The output is used by the deterministic_entailment_test to check whether a
prediction's relation graph is fully encoded in the evidence.
"""
from __future__ import annotations

import re
import json
import hashlib
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Relational verbs -> canonical causal types
CAUSAL_VERBS = {
    # CAUSES (X makes Y happen / produces Y)
    "causes": "CAUSES", "cause": "CAUSES", "caused": "CAUSES",
    "produces": "CAUSES", "produce": "CAUSES", "produced": "CAUSES",
    "triggers": "CAUSES", "trigger": "CAUSES", "triggered": "CAUSES",
    "induces": "CAUSES", "induce": "CAUSES", "induced": "CAUSES",
    "generates": "CAUSES", "generate": "CAUSES", "generated": "CAUSES",
    "creates": "CAUSES", "create": "CAUSES", "created": "CAUSES",
    "leads": "CAUSES",  # "leads to"
    "results": "CAUSES",  # "results in"

    # ENABLES (X allows Y to happen / makes Y possible)
    "enables": "ENABLES", "enable": "ENABLES", "enabled": "ENABLES",
    "allows": "ENABLES", "allow": "ENABLES", "allowed": "ENABLES",
    "permits": "ENABLES", "permit": "ENABLES", "permitted": "ENABLES",
    "facilitates": "ENABLES", "facilitate": "ENABLES",
    "supports": "ENABLES", "support": "ENABLES", "supported": "ENABLES",
    "can": "ENABLES",  # "X can Y"
    "uses": "ENABLES", "use": "ENABLES", "used": "ENABLES",  # "X uses Y"

    # PREVENTS / INHIBITS (X stops Y)
    "prevents": "PREVENTS", "prevent": "PREVENTS", "prevented": "PREVENTS",
    "blocks": "PREVENTS", "block": "PREVENTS", "blocked": "PREVENTS",
    "inhibits": "PREVENTS", "inhibit": "PREVENTS", "inhibited": "PREVENTS",
    "suppresses": "PREVENTS", "suppress": "PREVENTS", "suppressed": "PREVENTS",
    "limits": "PREVENTS", "limit": "PREVENTS", "limited": "PREVENTS",
    "reduces": "PREVENTS", "reduce": "PREVENTS", "reduced": "PREVENTS",

    # INCREASES / DECREASES (directional)
    "increases": "INCREASES", "increase": "INCREASES", "increased": "INCREASES",
    "improves": "INCREASES", "improve": "INCREASES", "improved": "INCREASES",
    "enhances": "INCREASES", "enhance": "INCREASES", "enhanced": "INCREASES",
    "boosts": "INCREASES", "boost": "INCREASES", "boosted": "INCREASES",
    "decreases": "DECREASES", "decrease": "DECREASES", "decreased": "DECREASES",
    "lowers": "DECREASES", "lower": "DECREASES", "lowered": "DECREASES",
    "worsens": "DECREASES", "worsen": "DECREASES", "worsened": "DECREASES",

    # EXHIBITS / SHOWS (relational, not causal)
    "exhibits": "EXHIBITS", "exhibit": "EXHIBITS", "exhibited": "EXHIBITS",
    "shows": "EXHIBITS", "show": "EXHIBITS", "showed": "EXHIBITS", "shown": "EXHIBITS",
    "demonstrates": "EXHIBITS", "demonstrate": "EXHIBITS", "demonstrated": "EXHIBITS",
    "displays": "EXHIBITS", "display": "EXHIBITS", "displayed": "EXHIBITS",
    "has": "EXHIBITS", "have": "EXHIBITS", "had": "EXHIBITS",
    "contains": "EXHIBITS", "contain": "EXHIBITS", "contained": "EXHIBITS",
    "is": "EXHIBITS", "are": "EXHIBITS", "was": "EXHIBITS", "were": "EXHIBITS",
}

# Stopwords for entity extraction
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "by",
    "for", "with", "from", "as", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "can", "shall", "that", "this",
    "these", "those", "which", "who", "whom", "whose", "what", "where", "when",
    "why", "how", "than", "then", "there", "here", "such", "same", "other",
    "some", "any", "all", "no", "not", "only", "just", "very", "more", "most",
    "less", "fewer", "much", "many", "few", "several", "various", "each",
    "every", "both", "either", "neither", "into", "onto", "upon", "within",
    "without", "through", "during", "before", "after", "since", "until",
    "between", "among", "against", "above", "below", "over", "under", "across",
    "along", "around", "behind", "beyond", "toward", "towards", "about",
    "they", "them", "their", "it", "its", "we", "us", "our", "you", "your",
    "he", "him", "his", "she", "her", "hers", "i", "me", "my", "mine",
    "due", "because", "while", "whereas", "although", "though", "even",
    "however", "therefore", "thus", "hence", "moreover", "furthermore",
    "nevertheless", "nonetheless", "accordingly", "consequently", "otherwise",
    "rather", "yet", "still", "already", "always", "never", "often",
    "sometimes", "usually", "rarely", "seldom", "indeed", "instead",
    "besides", "etc", "via", "per", "using", "used", "use", "uses",
    "high", "low", "higher", "lower", "high-energy", "non-aqueous",
    "reversible", "reversibly", "rechargeable", "stable", "unstable",
    "safe", "unsafe", "specific", "custom", "known", "considered",
    "broad", "narrow", "main", "minor", "major", "new", "old", "novel",
    "existing", "current", "present", "absent", "available", "possible",
    "impossible", "exist", "exists", "existed", "allow", "allows",
    "challenge", "problem", "issue", "limit", "limits", "limitation",
    "limitations", "barrier", "barriers", "obstacle", "obstacles",
}

GENERIC_NOUNS = {
    "approach", "method", "technique", "technology", "system", "process",
    "procedure", "step", "way", "means", "tool", "tools", "device", "devices",
    "material", "materials", "compound", "compounds", "structure",
    "structures", "property", "properties", "feature", "features",
    "characteristic", "characteristics", "aspect", "aspects", "factor",
    "factors", "element", "elements", "component", "components", "part",
    "parts", "phase", "phases", "stage", "stages", "state", "states",
    "form", "forms", "type", "types", "kind", "kinds", "sort", "sorts",
    "class", "classes", "category", "categories", "group", "groups",
    "set", "sets", "subset", "subsets", "case", "cases", "instance",
    "instances", "example", "examples", "sample", "samples", "specimen",
    "specimens", "subject", "subjects", "object", "objects", "item", "items",
    "thing", "things", "stuff", "matter", "substance", "substances",
    "result", "results", "outcome", "outcomes", "effect", "effects",
    "consequence", "consequences", "impact", "impacts", "influence",
    "influences", "finding", "findings", "observation", "observations",
    "data", "datum", "information", "knowledge", "evidence", "proof",
    "fact", "facts", "detail", "details", "study", "studies", "research",
    "experiment", "experiments", "experimentation", "test", "tests",
    "testing", "trial", "trials", "evaluation", "evaluations",
    "assessment", "assessments", "analysis", "analyses", "measurement",
    "measurements", "value", "values", "number", "numbers", "amount",
    "amounts", "quantity", "quantities", "level", "levels", "rate", "rates",
    "ratio", "ratios", "fraction", "fractions", "percentage", "percentages",
    "proportion", "proportions", "concentration", "concentrations",
    "prediction", "predictions", "hypothesis", "hypotheses", "theory",
    "theories", "model", "models", "framework", "frameworks", "concept",
    "concepts", "idea", "ideas", "notion", "notions", "view", "views",
    "opinion", "opinions", "perspective", "perspectives", "claim", "claims",
    "statement", "statements", "assertion", "assertions", "argument",
    "arguments", "reasoning", "logic", "principle", "principles", "law",
    "laws", "rule", "rules", "rule_set", "rule_sets", "criterion",
    "criteria", "standard", "standards", "specification", "specifications",
    "requirement", "requirements", "constraint", "constraints", "limit",
    "limits", "boundary", "boundaries", "scope", "context", "contexts",
    "situation", "situations", "scenario", "scenarios", "condition",
    "conditions", "environment", "environments", "setting", "settings",
    "background", "backgrounds", "history", "histories", "past", "future",
    "present", "current", "previous", "prior", "subsequent", "later",
    "earlier", "first", "second", "third", "final", "initial", "middle",
    "end", "beginning", "start", "finish", "completion", "initiation",
    "duration", "interval", "intervals", "period", "periods", "time",
    "times", "point", "points", "phase", "phases", "cycle", "cycles",
    "iteration", "iterations", "round", "rounds", "pass", "passes", "run",
    "runs", "execution", "executions", "operation", "operations",
    "function", "functions", "role", "roles", "purpose", "purposes",
    "goal", "goals", "objective", "objectives", "aim", "aims", "target",
    "targets", "end", "ends", "intention", "intentions", "intent",
    "design", "designs", "plan", "plans", "scheme", "schemes", "strategy",
    "strategies", "tactic", "tactics", "approach", "approaches",
}

NEGATION_PREFIXES = {"not", "no", "non", "cannot", "without", "rarely", "barely"}


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def extract_entities(text: str) -> dict:
    """Extract entity surface forms.

    Returns:
      {
        "proper_nouns":   [...],  # capitalized (>=4 chars), not sentence-initial
        "technical_nouns": [...], # lowercase content terms (>=5 chars)
        "chemicals":      [...],  # all-caps abbreviations or formula-like tokens
        "all":            [...]   # union
      }
    """
    text = text or ""

    # Proper nouns: capitalized tokens >=4 chars, NOT in first position of a sentence
    sentences = re.split(r"[.!?]\s+", text)
    proper = set()
    for sent in sentences:
        toks = sent.split()
        for i, tok in enumerate(toks):
            clean = re.sub(r"[^A-Za-z0-9]", "", tok)
            if len(clean) >= 4 and clean[0].isupper() and not clean.isupper():
                # Exclude sentence-initial common words
                if i == 0 and clean.lower() in {"intercalation", "graphite", "lithium",
                                                  "perovskite", "graphene", "silicon",
                                                  "dendrite", "batteries", "battery",
                                                  "solar", "cells", "vaccines",
                                                  "vaccine", "models", "model",
                                                  "compounds", "compound"}:
                    pass  # still include — these are domain terms that happen to start sentences
                proper.add(clean)

    # Chemicals: tokens like "LiCoO2", "DNA", "RNA", "PD-1", "Cas9", "mAh/g"
    chemicals = set()
    for m in re.finditer(r"\b([A-Z][a-zA-Z]{0,3}\d?(?:[A-Z][a-z]?\d?)*\d?)\b", text):
        tok = m.group(1)
        if len(tok) >= 2 and any(c.isdigit() for c in tok):
            chemicals.add(tok)
    for m in re.finditer(r"\b([A-Z]{2,}\d*)\b", text):
        tok = m.group(1)
        if len(tok) >= 2 and not tok.lower() in {"the", "and", "for", "but", "not",
                                                   "all", "any", "via", "etc"}:
            chemicals.add(tok)

    # Technical nouns: lowercase content terms >=5 chars
    tokens = re.findall(r"\b[a-z][a-z0-9_-]{4,}\b", text.lower())
    tech = set()
    for t in tokens:
        if t in STOPWORDS or t in GENERIC_NOUNS:
            continue
        tech.add(t)

    all_entities = sorted(proper | chemicals | tech)
    return {
        "proper_nouns": sorted(proper),
        "technical_nouns": sorted(tech),
        "chemicals": sorted(chemicals),
        "all": all_entities,
    }


# ---------------------------------------------------------------------------
# Mechanism / causal-edge extraction
# ---------------------------------------------------------------------------

def _split_simple_sentences(text: str) -> list[str]:
    """Split text into simple sentences on . ! ? and also on ' due to ', ' because '."""
    text = text or ""
    # Split on sentence boundaries
    sents = re.split(r"(?<=[.!?])\s+", text)
    # Further split on conjunctions that introduce new clauses
    out = []
    for s in sents:
        s = s.strip()
        if not s:
            continue
        # Split on ", and " / ", but " / "; " / " due to " / " because "
        parts = re.split(r"\s*(?:, and |, but |; | due to | because )\s*", s)
        out.extend(p.strip() for p in parts if p.strip())
    return out


def _extract_subject_predicate_object(sentence: str) -> tuple[str, str, str] | None:
    """Crude SVO extraction: subject ... VERB ... object."""
    s = sentence.strip().rstrip(".")
    # Find first causal verb in the sentence
    tokens = s.split()
    verb_idx = None
    verb_canonical = None
    for i, tok in enumerate(tokens):
        clean = re.sub(r"[^a-z]", "", tok.lower())
        if clean in CAUSAL_VERBS:
            verb_idx = i
            verb_canonical = CAUSAL_VERBS[clean]
            break
    if verb_idx is None or verb_idx == 0 or verb_idx >= len(tokens) - 1:
        return None
    subject = " ".join(tokens[:verb_idx]).strip()
    # Object = everything after the verb, up to the next clause boundary
    obj_tokens = tokens[verb_idx + 1:]
    # Cut at prepositional boundary or conjunction
    cut_idx = len(obj_tokens)
    for j, t in enumerate(obj_tokens):
        if re.sub(r"[^a-z]", "", t.lower()) in {"and", "but", "however", "while", "whereas", "although", "though"}:
            cut_idx = j
            break
    obj = " ".join(obj_tokens[:cut_idx]).strip().rstrip(",")
    if not subject or not obj:
        return None
    return subject, verb_canonical, obj


def extract_mechanisms_and_causal_edges(text: str) -> tuple[list[dict], list[dict]]:
    """Extract mechanism triples and causal edges."""
    text = text or ""
    sentences = _split_simple_sentences(text)

    mechanisms = []
    causal_edges = []

    for sent in sentences:
        svo = _extract_subject_predicate_object(sent)
        if not svo:
            continue
        subject, verb_type, obj = svo
        # Check for negation in the subject or sentence
        is_negated = any(re.sub(r"[^a-z]", "", w.lower()) in NEGATION_PREFIXES
                         for w in sent.split()[:3])

        mech = {
            "subject": subject.lower(),
            "predicate": verb_type,
            "object": obj.lower(),
            "negated": is_negated,
            "source_sentence": sent[:200],
        }
        mechanisms.append(mech)

        # Causal edge: subject --[verb_type]--> object
        if verb_type in {"CAUSES", "ENABLES", "PREVENTS", "INCREASES", "DECREASES"}:
            edge_type = "PREVENTS" if verb_type == "PREVENTS" else \
                        "INCREASES" if verb_type == "INCREASES" else \
                        "DECREASES" if verb_type == "DECREASES" else \
                        verb_type
            causal_edges.append({
                "cause": subject.lower(),
                "effect": obj.lower(),
                "type": edge_type,
                "negated": is_negated,
            })

    return mechanisms, causal_edges


# ---------------------------------------------------------------------------
# Combination extraction
# ---------------------------------------------------------------------------

def extract_combinations(text: str) -> list[dict]:
    """Extract explicit combinations: 'X and Y' / 'X combined with Y' / 'X + Y'."""
    text = text or ""
    combos = []
    # "X and Y" — where X and Y are both noun-like
    for m in re.finditer(r"\b([A-Za-z][A-Za-z0-9_-]{2,})\s+(?:and|combined with|plus|\+)\s+([A-Za-z][A-Za-z0-9_-]{2,})\b", text):
        a, b = m.group(1).lower(), m.group(2).lower()
        if a in STOPWORDS or b in STOPWORDS:
            continue
        combos.append({"a": a, "b": b, "raw": m.group(0)})
    return combos


# ---------------------------------------------------------------------------
# Constraint extraction
# ---------------------------------------------------------------------------

def extract_constraints(text: str) -> list[dict]:
    """Extract explicit constraints / quantitative statements."""
    text = text or ""
    constraints = []
    # Pattern: "<subject> <relation> <value/unit>"
    # Examples:
    #   "LiCoO2 has been shown to intercalate lithium"
    #   "efficiency ~11%"
    #   "cycle life > 100"
    #   ">500 cycles"
    #   "thermodynamically unstable"
    for sent in _split_simple_sentences(text):
        s = sent.strip().rstrip(".")
        # Numeric constraint
        m = re.search(r"(.+?)\s+(>=?|<=?|~|approximately|about|around|less than|more than|above|below|over|under)\s*(\d+(?:\.\d+)?)\s*([A-Za-z/%]*)", s, re.I)
        if m:
            constraints.append({
                "subject": m.group(1).strip().lower()[:100],
                "relation": m.group(2).lower(),
                "value": float(m.group(3)),
                "unit": m.group(4).lower(),
                "type": "NUMERIC",
                "source_sentence": sent[:200],
            })
            continue
        # Property assertion (no number): "X is Y" / "X are Y" / "X has Y"
        m = re.search(r"\b([A-Za-z][A-Za-z0-9_-]{2,})\s+(?:is|are|was|were|has|have|exhibits?|shows?)\s+([a-z][a-z-]{3,})", s, re.I)
        if m:
            sub = m.group(1).lower()
            obj = m.group(2).lower()
            if sub in STOPWORDS or obj in STOPWORDS:
                continue
            if obj in GENERIC_NOUNS:
                continue
            constraints.append({
                "subject": sub,
                "relation": "PROPERTY",
                "value": obj,
                "unit": "",
                "type": "PROPERTY",
                "source_sentence": sent[:200],
            })
    return constraints


# ---------------------------------------------------------------------------
# Negation extraction
# ---------------------------------------------------------------------------

def extract_negations(text: str) -> list[str]:
    """Extract explicit negative statements."""
    text = text or ""
    negs = []
    for sent in _split_simple_sentences(text):
        s = sent.strip().rstrip(".")
        if re.search(r"\b(not|no|non-|cannot|cannot|without|rarely|barely|un-|in-|impossible|unstable|unsafe|unable)\b", s, re.I):
            negs.append(s[:200])
    return negs


# ---------------------------------------------------------------------------
# Top-level extraction
# ---------------------------------------------------------------------------

def extract_structured_evidence(evidence_text: str, case_id: str = "") -> dict:
    """Extract structured evidence object from raw text."""
    entities = extract_entities(evidence_text)
    mechanisms, causal_edges = extract_mechanisms_and_causal_edges(evidence_text)
    combinations = extract_combinations(evidence_text)
    constraints = extract_constraints(evidence_text)
    negations = extract_negations(evidence_text)

    obj = {
        "case_id": case_id,
        "entities": entities["all"],
        "entities_proper_nouns": entities["proper_nouns"],
        "entities_technical_nouns": entities["technical_nouns"],
        "entities_chemicals": entities["chemicals"],
        "mechanisms": mechanisms,
        "causal_edges": causal_edges,
        "combinations": combinations,
        "constraints": constraints,
        "negations": negations,
        "raw_text": evidence_text,
        "extraction_method": "deterministic_regex_v1",
        "n_entities": len(entities["all"]),
        "n_mechanisms": len(mechanisms),
        "n_causal_edges": len(causal_edges),
        "n_combinations": len(combinations),
        "n_constraints": len(constraints),
        "n_negations": len(negations),
    }

    # Hash for immutability
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    obj["evidence_object_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return obj


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import sys
    REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
    BENCHMARK = REPO / "discovery_fabric/v1_13/benchmark_dataset.json"
    OUT_DIR = REPO / "discovery_fabric/v1_13_gate2/evidence_objects"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(BENCHMARK) as f:
        cases = json.load(f)

    print(f"Extracting structured evidence for {len(cases)} cases...")
    for case in cases:
        ev_obj = extract_structured_evidence(case["pre_outcome_evidence"], case["id"])
        out_path = OUT_DIR / f"{case['id']}.json"
        with open(out_path, "w") as f:
            json.dump(ev_obj, f, indent=2, ensure_ascii=False)
        print(f"  {case['id']} ({case['name']}): "
              f"{ev_obj['n_entities']} entities, {ev_obj['n_mechanisms']} mechanisms, "
              f"{ev_obj['n_causal_edges']} edges, {ev_obj['n_constraints']} constraints")

    print(f"\nDone. Evidence objects saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
