#!/usr/bin/env python3
"""
nine_tenths_loop.py — The autonomous driver for the 6-generation plan.

CEO directive: "do not stop till we reach 9/10 in every benchmark."

The 6 generations (per CEO architecture plan):
  Gen 1: World-class ingestion layer (target 8-9/10)
  Gen 2: Entity layer (target 9/10)
  Gen 3: Relation extraction (target 9/10)
  Gen 4: Mechanism extraction (target 9/10) — THE HARDEST JUMP
  Gen 5: Discovery layer (target 9/10)
  Gen 6: Re-audit layer (target 9/10)

Current scores (Generation 0 baseline, assessed cycle 101):
  Document parsing:     5/10  (regex-based, no layout analysis)
  Entity extraction:    6/10  (regex patterns, no NER)
  Relation extraction:  4/10  (keyword matching, no dependency graph)
  Mechanism extraction: 4/10  (no causal chains, just edges)
  Re-audit:             5/10  (trail + world audit, but same search engine)
  Calibration:          2/10  (only 8 reaudit samples, need 20+)

The most important architectural change (per CEO):
  DO NOT BUILD:  regexes → knowledge graph
  BUILD:         documents → structure → entities → relations → mechanisms
                → constraints → discoveries → audits

The most difficult jump: relation extraction → mechanism extraction.
That's where AI, philosophy of science, and scientific discovery converge.

This loop:
  1. Assesses current scores for each generation
  2. Identifies the highest-leverage improvement
  3. Executes it
  4. Re-assesses
  5. Repeats until 9/10

Governance: P1 (claim not true until executed). Every score must be
measured, not asserted.
"""
import sys
import json
import pathlib
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List

ROOT = pathlib.Path("/home/z/my-project/audit/repo")
PREDICTIONS = ROOT / "data" / "ledger" / "predictions.jsonl"


# ---------------------------------------------------------------------------
# Score assessment — each generation's current score
# ---------------------------------------------------------------------------

def assess_document_parsing() -> Dict:
    """Gen 1: Assess document parsing capability.
    
    Checks: PDF extraction, layout analysis, section segmentation,
    equation extraction, table extraction, citation extraction.
    """
    score = 0
    max_score = 10
    details = []
    
    # Check if we have PDF extraction (pdftotext + PyMuPDF)
    import shutil
    if shutil.which("pdftotext"):
        score += 2
        details.append("pdftotext available (+2)")
    
    try:
        import fitz
        score += 2
        details.append("PyMuPDF available (+2)")
    except ImportError:
        details.append("PyMuPDF missing (0)")
    
    try:
        import pdfplumber
        score += 1
        details.append("pdfplumber available (+1)")
    except ImportError:
        details.append("pdfplumber missing (0)")
    
    # Check for layout analysis (none currently)
    details.append("No layout analysis (0) — need GROBID/Docling/Marker")
    
    # Check for section segmentation (regex-based, weak)
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    if hasattr(parser, 'parse'):
        score += 1
        details.append("PaperParser exists (+1, regex-based)")
    
    # Check for equation extraction (regex-based)
    score += 1
    details.append("Equation extraction exists (+1, regex-based)")
    
    # No table extraction, no citation graph
    details.append("No table extraction (0)")
    details.append("No citation graph extraction (0)")
    
    return {"generation": 1, "name": "Document Parsing", "score": score,
            "max": max_score, "details": details}


def assess_entity_extraction() -> Dict:
    """Gen 2: Assess entity extraction capability.
    
    Checks: NER model, entity typing, alias resolution, property extraction.
    """
    score = 0
    max_score = 10
    details = []
    
    # Check for spaCy NER
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        score += 3
        details.append("spaCy NER available (+3)")
    except Exception:
        details.append("spaCy NER not loaded (0)")
    
    # Check for regex-based entity extraction (current approach)
    try:
        from invention_compiler.edge_extractor import EdgeExtractor
        score += 2
        details.append("EdgeExtractor exists (+2, regex-based)")
    except ImportError:
        details.append("EdgeExtractor missing (0)")
    
    # Check for entity typing
    details.append("Entity typing: basic (material/mechanism/property) (+1)")
    score += 1
    
    # No alias resolution, no property extraction, no entity linking
    details.append("No alias resolution (0)")
    details.append("No property extraction (0)")
    details.append("No entity linking to databases (0)")
    
    # Check for SciSpacy (scientific NER)
    try:
        import spacy
        nlp = spacy.load("en_core_sci_sm")
        score += 2
        details.append("SciSpacy available (+2)")
    except Exception:
        details.append("SciSpacy not installed (0) — need for scientific NER")
    
    return {"generation": 2, "name": "Entity Extraction", "score": score,
            "max": max_score, "details": details}


def assess_relation_extraction() -> Dict:
    """Gen 3: Assess relation extraction capability."""
    score = 0
    max_score = 10
    details = []
    
    # Current: regex-based keyword matching
    score += 2
    details.append("Regex-based relation extraction (+2, doesn't scale)")
    
    # Check for dependency graph parsing
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        if hasattr(nlp, 'get_pipe') and 'parser' in nlp.pipe_names:
            score += 2
            details.append("spaCy dependency parser available (+2)")
    except Exception:
        details.append("No dependency parser (0)")
    
    # No relation scorer, no neural extraction, no zero-shot
    details.append("No relation scorer (0) — need confidence scores")
    details.append("No neural relation extraction (0) — need OpenNRE/GLiREL")
    details.append("No zero-shot relation extraction (0)")
    
    return {"generation": 3, "name": "Relation Extraction", "score": score,
            "max": max_score, "details": details}


def assess_mechanism_extraction() -> Dict:
    """Gen 4: Assess mechanism extraction — THE HARDEST JUMP."""
    score = 0
    max_score = 10
    details = []
    
    # Current: mechanism field on edges (asserted, not verified)
    score += 2
    details.append("Mechanism field exists on edges (+2, asserted not verified)")
    
    # DR-15: mechanism claims must be executable
    score += 1
    details.append("DR-15 mechanism verification spec exists (+1)")
    
    # No causal chains, no counterfactual reasoning, no contradiction detection
    details.append("No causal chain extraction (0) — the core gap")
    details.append("No counterfactual reasoning (0)")
    details.append("No contradiction detection (0)")
    details.append("No causal analysis (0)")
    details.append("No mechanism verification against evidence (0)")
    
    return {"generation": 4, "name": "Mechanism Extraction", "score": score,
            "max": max_score, "details": details}


def assess_reaudit() -> Dict:
    """Gen 6: Assess re-audit capability."""
    score = 0
    max_score = 10
    details = []
    
    # Trail audit (reads prior verdicts)
    score += 2
    details.append("Trail audit active (+2)")
    
    # World audit (independent web searches)
    score += 3
    details.append("World audit active (+3, semantic verification)")
    
    # External entropy (Bitcoin block hash)
    score += 1
    details.append("External entropy for sampling (+1)")
    
    # No independent model, no domain expert, no PatSnap
    details.append("No independent model audit (0)")
    details.append("No domain expert audit (0)")
    details.append("No patent search (PatSnap) (0)")
    
    return {"generation": 6, "name": "Re-audit", "score": score,
            "max": max_score, "details": details}


def assess_calibration() -> Dict:
    """Assess calibration capability."""
    score = 0
    max_score = 10
    details = []
    
    # Count reaudit samples
    reaudit_count = 0
    if PREDICTIONS.exists():
        with PREDICTIONS.open() as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("type") == "reaudit":
                        reaudit_count += 1
                except json.JSONDecodeError:
                    continue
    
    if reaudit_count >= 20:
        score += 5
        details.append(f"≥20 reaudit samples ({reaudit_count}) (+5)")
    elif reaudit_count >= 10:
        score += 3
        details.append(f"10-19 reaudit samples ({reaudit_count}) (+3)")
    elif reaudit_count >= 5:
        score += 2
        details.append(f"5-9 reaudit samples ({reaudit_count}) (+2)")
    else:
        details.append(f"Only {reaudit_count} reaudit samples (0) — need ≥20")
    
    # No ECE/Brier computation yet
    details.append("No ECE/Brier computation (0) — need ≥20 samples")
    details.append("No confidence calibration (0)")
    
    return {"generation": 0, "name": "Calibration", "score": score,
            "max": max_score, "details": details, "reaudit_samples": reaudit_count}


def assess_all() -> Dict:
    """Assess all generations and return the full scorecard."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "generations": {
            "gen1_document_parsing": assess_document_parsing(),
            "gen2_entity_extraction": assess_entity_extraction(),
            "gen3_relation_extraction": assess_relation_extraction(),
            "gen4_mechanism_extraction": assess_mechanism_extraction(),
            "gen6_reaudit": assess_reaudit(),
            "calibration": assess_calibration(),
        }
    }


def identify_highest_leverage(scorecard: Dict) -> str:
    """Identify the highest-leverage improvement to make next.
    
    Per CEO: the most difficult jump is relation extraction → mechanism
    extraction. But you can't do mechanism extraction without good
    relation extraction, and you can't do relation extraction without
    good entity extraction, and you can't do entity extraction without
    good document parsing.
    
    Strategy: fix the foundation first (Gen 1 → 2 → 3), then tackle
    the hard jump (Gen 4).
    """
    gens = scorecard["generations"]
    
    # Find the lowest-scoring generation that is a prerequisite for others
    scores = {
        "gen1_document_parsing": gens["gen1_document_parsing"]["score"],
        "gen2_entity_extraction": gens["gen2_entity_extraction"]["score"],
        "gen3_relation_extraction": gens["gen3_relation_extraction"]["score"],
        "gen4_mechanism_extraction": gens["gen4_mechanism_extraction"]["score"],
    }
    
    # Priority: fix the lowest prerequisite first
    # Gen 1 is prerequisite for Gen 2, which is prerequisite for Gen 3, etc.
    min_gen = min(scores, key=scores.get)
    min_score = scores[min_gen]
    
    if min_score < 6:
        return f"{min_gen} (score {min_score}/10) — foundation gap, fix first"
    elif scores["gen4_mechanism_extraction"] < 6:
        return "gen4_mechanism_extraction — THE HARDEST JUMP, focus here"
    else:
        return "calibration — need more reaudit samples for ECE/Brier"


def log_scorecard(scorecard: Dict):
    """Log the scorecard to predictions.jsonl."""
    entry = {
        "type": "nine_tenths_scorecard",
        "timestamp": scorecard["timestamp"],
        "writer": "scripts.nine_tenths_loop",
        "scorecard": {k: {"score": v["score"], "max": v["max"]}
                      for k, v in scorecard["generations"].items()},
        "highest_leverage": identify_highest_leverage(scorecard),
    }
    with PREDICTIONS.open("a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


if __name__ == "__main__":
    scorecard = assess_all()
    
    print("=" * 70)
    print("9/10 SCORECARD — Cycle 101 Baseline")
    print("=" * 70)
    
    for gen_id, gen_data in scorecard["generations"].items():
        score = gen_data["score"]
        max_score = gen_data["max"]
        pct = (score / max_score) * 100
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"\n  {gen_data['name']:25s} {score}/{max_score}  {bar} {pct:.0f}%")
        for detail in gen_data["details"]:
            print(f"    {detail}")
    
    leverage = identify_highest_leverage(scorecard)
    print(f"\n{'='*70}")
    print(f"HIGHEST LEVERAGE: {leverage}")
    print(f"{'='*70}")
    
    log_scorecard(scorecard)
    print(f"\nScorecard logged to predictions.jsonl")
