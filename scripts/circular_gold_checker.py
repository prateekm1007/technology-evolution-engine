#!/usr/bin/env python3
"""
circular_gold_checker.py — DR-75: Detect gold-standard contamination.

The "gold standard" is the measurement or validation data used to check
a candidate's prediction. If the gold standard has been CONTAMINATED by
the input — e.g., bridge words from the input spec appear verbatim in
the gold data — then any "pass" against the gold is meaningless.

The checker inspects:
  - The input text (spec, source material, prompt)
  - The gold-standard data (test set, validation set)
  - And flags overlap in distinctive "bridge" phrases (multi-word n-grams
    that are unlikely to occur by chance).

Adversarial test: if you inject bridge phrases from the input into the
gold data, the checker MUST flag contamination.

Usage:
    from scripts.circular_gold_checker import CircularGoldChecker
    checker = CircularGoldChecker()
    report = checker.check(input_text, gold_text)
    # report.is_contaminated == True/False
"""
import sys
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class ContaminationHit:
    """One bridge-phrase contamination hit."""
    phrase: str
    input_location: str = ""
    gold_location: str = ""


@dataclass
class ContaminationReport:
    """The output of CircularGoldChecker.check()."""
    is_contaminated: bool = False
    n_hits: int = 0
    hits: List[ContaminationHit] = field(default_factory=list)
    bridge_phrases_found: List[str] = field(default_factory=list)
    input_length: int = 0
    gold_length: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_contaminated": self.is_contaminated,
            "n_hits": self.n_hits,
            "hits": [h.__dict__ for h in self.hits],
            "bridge_phrases_found": self.bridge_phrases_found,
            "input_length": self.input_length,
            "gold_length": self.gold_length,
            "timestamp": self.timestamp,
        }


# Stopwords (don't count as bridge phrases on their own).
STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "but",
    "with", "without", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "at", "by", "from",
    "into", "about", "than", "then", "so", "if", "but", "because",
}


class CircularGoldChecker:
    """DR-75: detect gold-standard contamination by bridge phrases."""

    def __init__(self, min_phrase_len: int = 3, min_phrase_chars: int = 8,
                 max_phrases: int = 50):
        """Args:
            min_phrase_len: minimum number of words in a bridge phrase
            min_phrase_chars: minimum number of characters
            max_phrases: cap on number of phrases to extract (perf)
        """
        self.min_phrase_len = min_phrase_len
        self.min_phrase_chars = min_phrase_chars
        self.max_phrases = max_phrases

    # ----- public API ---------------------------------------------------
    def check(self, input_text: str, gold_text: str) -> ContaminationReport:
        """Check whether gold_text is contaminated by input_text.

        Args:
            input_text: the input (spec, source, prompt)
            gold_text: the gold-standard data

        Returns:
            ContaminationReport with is_contaminated flag
        """
        input_phrases = self._extract_phrases(input_text)
        gold_lower = gold_text.lower()
        hits: List[ContaminationHit] = []
        bridge_found: List[str] = []
        for phrase in input_phrases:
            if phrase in gold_lower:
                hits.append(ContaminationHit(
                    phrase=phrase,
                    input_location="input",
                    gold_location="gold",
                ))
                bridge_found.append(phrase)
                if len(hits) >= 20:  # cap reported hits
                    break

        return ContaminationReport(
            is_contaminated=len(hits) > 0,
            n_hits=len(hits),
            hits=hits,
            bridge_phrases_found=bridge_found,
            input_length=len(input_text),
            gold_length=len(gold_text),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def check_batch(self, input_text: str,
                    gold_texts: Dict[str, str]) -> Dict[str, ContaminationReport]:
        """Check multiple gold texts against one input."""
        return {k: self.check(input_text, v) for k, v in gold_texts.items()}

    # ----- internals ----------------------------------------------------
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract distinctive multi-word phrases from text.

        A "phrase" is a contiguous n-gram of length >= min_phrase_len,
        where the first and last tokens are NOT stopwords. Stopwords
        may appear INSIDE the phrase (e.g., "thermoelectric figure of
        merit ZT" is a valid 5-gram). Returns lowercase phrases.
        """
        # Tokenize (keep only word characters)
        tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
        phrases: List[str] = []
        # Generate n-grams of length min_phrase_len to (min_phrase_len + 4)
        max_n = self.min_phrase_len + 4
        for n in range(self.min_phrase_len, min(max_n, len(tokens)) + 1):
            for i in range(len(tokens) - n + 1):
                window = tokens[i:i + n]
                # Skip if the first or last token is a stopword
                if window[0] in STOPWORDS or window[-1] in STOPWORDS:
                    continue
                # Skip if ALL tokens are stopwords
                if all(t in STOPWORDS for t in window):
                    continue
                phrase = " ".join(window)
                if len(phrase) >= self.min_phrase_chars:
                    phrases.append(phrase)
                    if len(phrases) >= self.max_phrases:
                        return phrases
        return phrases


def main():
    print("=" * 60)
    print("CIRCULAR GOLD CHECKER (DR-75)")
    print("=" * 60)
    print()

    checker = CircularGoldChecker()

    input_text = ("We aim to improve the thermoelectric figure of merit "
                  "ZT of bismuth telluride by nanostructuring.")
    gold_clean = ("The reference dataset contains measurements of "
                  "Seebeck coefficient, electrical conductivity, and "
                  "thermal conductivity for various lead alloys.")
    gold_dirty = ("Validation uses the thermoelectric figure of merit ZT "
                  "of bismuth telluride by nanostructuring as ground truth.")

    r1 = checker.check(input_text, gold_clean)
    r2 = checker.check(input_text, gold_dirty)
    print(f"Clean gold:  contaminated={r1.is_contaminated} hits={r1.n_hits}")
    print(f"Dirty gold:  contaminated={r2.is_contaminated} hits={r2.n_hits}")
    print(f"  Bridge phrases found: {r2.bridge_phrases_found}")


if __name__ == "__main__":
    main()
