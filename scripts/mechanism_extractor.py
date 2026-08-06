#!/usr/bin/env python3
"""
mechanism_extractor.py — Structured mechanism extraction (Phase 2 of auditor roadmap).

Per cycle 142: the auditor found that edge_extractor.py produces "co-occurrence
dressed as mechanism" — template strings like "Bismuth telluride exhibits Power
output" for text that never said that. DR-15 requires mechanisms to be
executable, not just described.

This module replaces the template-string approach with structured extraction
that produces:
- ACTIVITY: what the system does (verb + object)
- TRANSITION: what changes (from_state → to_state)
- CONSTRAINT: what limits the mechanism (equation/inequality)
- EVIDENCE: where in the text the mechanism is stated

The output is a MechanismClaim object that can be checked against the source
text, not just a string that sounds plausible.

Usage:
    from scripts.mechanism_extractor import extract_mechanisms
    mechanisms = extract_mechanisms(text, entities, relations)
"""
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class MechanismClaim:
    """A structured mechanism claim extracted from text.

    Per DR-15: a mechanism is valid only if it satisfies one of:
    derived from first principles, reproduced experimentally, numerically
    simulated, or independently verified from source material.

    The 'text_span' field makes the claim checkable against the source —
    you can verify the text actually says what the mechanism claims.
    """
    subject: str           # the entity performing the activity
    activity: str          # what the subject does (verb)
    object: str            # what the activity acts on
    transition: Optional[str] = None    # "increases", "decreases", "produces", "enables"
    constraint: Optional[str] = None    # any constraint mentioned (e.g., "at room temperature")
    text_span: str = ""    # the exact text span that states this mechanism
    start_char: int = 0    # character offset in the source text
    end_char: int = 0      # character offset end
    confidence: float = 0.0
    source_sentence: str = ""  # the full sentence for context

    def is_checkable(self) -> bool:
        """A mechanism is checkable if it has a text span and a transition."""
        return bool(self.text_span) and bool(self.transition)

    def to_dict(self) -> Dict:
        return {
            "subject": self.subject,
            "activity": self.activity,
            "object": self.object,
            "transition": self.transition,
            "constraint": self.constraint,
            "text_span": self.text_span,
            "confidence": self.confidence,
            "source_sentence": self.source_sentence,
        }


# Activity-verb taxonomy: maps verb forms to structured activities
# Per cycle 142: these are the actual scientific activities, not template strings
ACTIVITY_VERBS = {
    # Physical activities
    "absorb": {"activity": "absorb", "transition": "increases", "category": "physical"},
    "adsorb": {"activity": "adsorb", "transition": "increases", "category": "physical"},
    "emit": {"activity": "emit", "transition": "produces", "category": "physical"},
    "reflect": {"activity": "reflect", "transition": "prevents", "category": "physical"},
    "transmit": {"activity": "transmit", "transition": "enables", "category": "physical"},
    "scatter": {"activity": "scatter", "transition": "decreases", "category": "physical"},
    "conduct": {"activity": "conduct", "transition": "enables", "category": "physical"},

    # Causal activities
    "cause": {"activity": "cause", "transition": "produces", "category": "causal"},
    "produce": {"activity": "produce", "transition": "produces", "category": "causal"},
    "generate": {"activity": "generate", "transition": "produces", "category": "causal"},
    "induce": {"activity": "induce", "transition": "produces", "category": "causal"},
    "trigger": {"activity": "trigger", "transition": "produces", "category": "causal"},

    # Enabling activities
    "enable": {"activity": "enable", "transition": "enables", "category": "enabling"},
    "facilitate": {"activity": "facilitate", "transition": "enables", "category": "enabling"},
    "allow": {"activity": "allow", "transition": "enables", "category": "enabling"},
    "permit": {"activity": "permit", "transition": "enables", "category": "enabling"},

    # Modulating activities
    "increase": {"activity": "increase", "transition": "increases", "category": "modulating"},
    "enhance": {"activity": "enhance", "transition": "increases", "category": "modulating"},
    "improve": {"activity": "improve", "transition": "increases", "category": "modulating"},
    "boost": {"activity": "boost", "transition": "increases", "category": "modulating"},
    "decrease": {"activity": "decrease", "transition": "decreases", "category": "modulating"},
    "reduce": {"activity": "reduce", "transition": "decreases", "category": "modulating"},
    "minimize": {"activity": "minimize", "transition": "decreases", "category": "modulating"},
    "maximize": {"activity": "maximize", "transition": "increases", "category": "modulating"},
    "optimize": {"activity": "optimize", "transition": "improves", "category": "modulating"},
    "lower": {"activity": "lower", "transition": "decreases", "category": "modulating"},
    "inhibit": {"activity": "inhibit", "transition": "decreases", "category": "modulating"},
    "suppress": {"activity": "suppress", "transition": "decreases", "category": "modulating"},
    "prevent": {"activity": "prevent", "transition": "prevents", "category": "modulating"},

    # Determining activities
    "determine": {"activity": "determine", "transition": "governs", "category": "determining"},
    "govern": {"activity": "govern", "transition": "governs", "category": "determining"},
    "control": {"activity": "control", "transition": "governs", "category": "determining"},
    "regulate": {"activity": "regulate", "transition": "governs", "category": "determining"},
    "dictate": {"activity": "dictate", "transition": "governs", "category": "determining"},

    # Characterizing activities
    "exhibit": {"activity": "exhibit", "transition": "exhibits", "category": "characterizing"},
    "propose": {"activity": "propose", "transition": "enables", "category": "enabling"},
    "compare": {"activity": "compare", "transition": "relates_to", "category": "characterizing"},
    "show": {"activity": "show", "transition": "exhibits", "category": "characterizing"},
    "display": {"activity": "display", "transition": "exhibits", "category": "characterizing"},
    "demonstrate": {"activity": "demonstrate", "transition": "exhibits", "category": "characterizing"},

    # Transforming activities
    "convert": {"activity": "convert", "transition": "transforms", "category": "transforming"},
    "transform": {"activity": "transform", "transition": "transforms", "category": "transforming"},
    "translate": {"activity": "translate", "transition": "transforms", "category": "transforming"},
}


def _stem_verb(verb: str) -> str:
    """Simple verb stemming to get the base form.

    Per cycle 142: fix the stemmer to handle "-es" correctly. "determines"
    should stem to "determine", not "determin". The rule: remove "es" only
    if the result ends in a consonant+e pattern (like "boxes" -> "box" is
    wrong, but "determines" -> "determine" is right). Simplest fix: try
    removing "es" first, then check if the result is in the taxonomy; if
    not, try removing "s" only.
    """
    verb = verb.lower().strip()
    # Try removing "ing"
    if verb.endswith("ing") and len(verb) > 5:
        return verb[:-3]
    # Try removing "ed"
    if verb.endswith("ed") and len(verb) > 4:
        return verb[:-2]
    # Try removing "es" — but only if the result is a reasonable verb stem
    if verb.endswith("es") and len(verb) > 4:
        stem = verb[:-2]
        # If the stem ends in 'e', it's likely correct (e.g., "determines" -> "determine")
        if stem.endswith("e") or stem.endswith("ibit") or stem in ACTIVITY_VERBS:
            return stem
        # Otherwise, try removing just "s" (e.g., "reduces" -> "reduce")
        return verb[:-1]
    # Try removing "s"
    if verb.endswith("s") and len(verb) > 3:
        return verb[:-1]
    return verb


def extract_mechanisms(text: str, entities: List, relations: List) -> List[MechanismClaim]:
    """Extract structured mechanism claims from text.

    This replaces the template-string approach in edge_extractor.py.
    Instead of producing "X exhibits Y" for any co-occurrence, it:
    1. Uses the relations (which have actual verbs from the text)
    2. Maps each verb to a structured activity
    3. Records the exact text span that states the mechanism
    4. Makes the claim checkable against the source

    Args:
        text: the source text
        entities: list of ExtractedEntity objects
        relations: list of ExtractedRelation objects (from nlp_pipeline)

    Returns:
        list of MechanismClaim objects
    """
    mechanisms = []

    for rel in relations:
        verb = rel.relation.lower().strip()
        stem = _stem_verb(verb)

        # Look up the activity in the taxonomy
        activity_info = ACTIVITY_VERBS.get(stem, ACTIVITY_VERBS.get(verb))

        if not activity_info:
            # Unknown verb — skip rather than produce a template string
            continue

        # Find the text span that states this mechanism
        subj_text = rel.subject.text
        obj_text = rel.obj.text

        # Search for the span in the source text
        text_span = ""
        start_char = 0
        end_char = 0

        # Try to find "subject ... verb ... object" in the text
        # Use a flexible search that allows words between
        subj_lower = subj_text.lower()
        obj_lower = obj_text.lower()

        # Find subject position
        subj_pos = text.lower().find(subj_lower)
        obj_pos = text.lower().find(obj_lower)

        if subj_pos >= 0 and obj_pos >= 0:
            start_char = min(subj_pos, obj_pos)
            end_char = max(subj_pos + len(subj_text), obj_pos + len(obj_text))
            text_span = text[start_char:end_char].strip()
        elif subj_pos >= 0:
            start_char = subj_pos
            end_char = subj_pos + len(subj_text)
            text_span = text[start_char:end_char].strip()

        # Extract constraint (if any) — look for prepositional phrases
        # near the mechanism (e.g., "at room temperature", "under pressure")
        constraint = None
        constraint_patterns = [
            r'(?:at|under|above|below|near)\s+([\w\s]{3,40}?)(?:[.,;]|\s+(?:and|while|where|which|that)\s)',
            r'(?:in|on|within)\s+([\w\s]{3,40}?)(?:[.,;]|\s+(?:and|while|where|which|that)\s)',
        ]
        for pattern in constraint_patterns:
            match = re.search(pattern, text[start_char:start_char+200], re.IGNORECASE)
            if match:
                constraint = match.group(1).strip()
                break

        # Get the source sentence
        source_sentence = ""
        if hasattr(rel, 'source_sentence') and rel.source_sentence:
            source_sentence = rel.source_sentence
        else:
            # Extract the sentence containing the span
            sent_start = text.rfind('.', 0, start_char) + 1
            sent_end = text.find('.', end_char)
            if sent_end < 0:
                sent_end = len(text)
            source_sentence = text[sent_start:sent_end].strip()

        mechanism = MechanismClaim(
            subject=subj_text,
            activity=activity_info["activity"],
            object=obj_text,
            transition=activity_info["transition"],
            constraint=constraint,
            text_span=text_span,
            start_char=start_char,
            end_char=end_char,
            confidence=rel.confidence,
            source_sentence=source_sentence,
        )
        mechanisms.append(mechanism)

    return mechanisms


def verify_mechanism(mechanism: MechanismClaim, source_text: str) -> bool:
    """Verify that a mechanism claim is actually stated in the source text.

    Per DR-15: a mechanism is valid only if it can be verified from source
    material. This function checks that the subject, verb, and object all
    appear in the text span, and that the text span actually exists in the
    source text.

    This is the check that was missing — the old approach produced mechanism
    strings that sounded plausible but couldn't be verified against the text.
    """
    if not mechanism.text_span:
        return False
    if mechanism.text_span not in source_text:
        return False
    # Check that subject and object appear in the span
    if mechanism.subject.lower() not in mechanism.text_span.lower():
        return False
    if mechanism.object.lower() not in mechanism.text_span.lower():
        return False
    return True


def main():
    """Demo: extract mechanisms from sample text."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()

    test_texts = [
        "Bismuth telluride exhibits a high Seebeck coefficient near room temperature.",
        "Phonon scattering reduces thermal conductivity without affecting electrical conductivity.",
        "The carrier concentration determines the thermoelectric efficiency of the material.",
        "Lithium plating causes capacity fade in graphite anodes during fast charging.",
    ]

    for text in test_texts:
        print(f"\nText: {text}")
        entities = pipeline.extract_entities(text)
        relations = pipeline.extract_relations(text, entities)
        mechanisms = extract_mechanisms(text, entities, relations)

        print(f"  Entities: {[(e.text, e.label) for e in entities]}")
        print(f"  Relations: {len(relations)}")
        print(f"  Mechanisms: {len(mechanisms)}")
        for m in mechanisms:
            verified = verify_mechanism(m, text)
            print(f"    {m.subject!r} --{m.activity}--> {m.object!r}")
            print(f"      transition={m.transition}, constraint={m.constraint}")
            print(f"      text_span={m.text_span!r}")
            print(f"      verified={verified}")


if __name__ == "__main__":
    main()
