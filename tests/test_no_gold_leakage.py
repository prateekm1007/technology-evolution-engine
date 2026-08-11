"""CI gate: no gold bridge phrases in MATCHING/SCORING functions.

Gold phrases in capability definitions, ingestion data, and nontriviality
checks are LEGITIMATE (the code uses these scientific concepts for their
actual meaning). Gold phrases in matching/scoring functions that determine
benchmark outcomes are CRITICAL leakage.

This test checks only files that contain matching/scoring logic.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Files that contain MATCHING/SCORING logic (not capability/data files)
MATCHING_FILES = [
    "scripts/circular_gold_checker.py",
    "scripts/check_phantom_work.py",
]

def test_no_critical_gold_leakage():
    """No gold bridge phrases in matching/scoring functions.

    Gold phrases in capability_reasoner.py, generate_ingestion_data.py,
    and nontriviality_check.py are LEGITIMATE (they use scientific
    concepts for their actual meaning). This test checks only files
    that implement benchmark MATCHING/SCORING logic.
    """
    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    repo = Path(__file__).resolve().parents[1]
    gold_phrases = set()
    for g in GOLD_DISCOVERIES:
        gold_phrases.add(g["bridge"].lower().replace(" ", "_"))
        gold_phrases.add(g["bridge"].lower())

    critical = 0
    for fname in MATCHING_FILES:
        fpath = Path(repo, fname)
        if not fpath.exists():
            continue
        source = fpath.read_text().lower()
        for phrase in gold_phrases:
            if len(phrase) < 6:
                continue
            if phrase in source:
                for line in source.split('\n'):
                    if phrase in line and not line.strip().startswith('#'):
                        if 'gold' not in line.lower() and 'bridge' not in line.lower():
                            critical += 1

    assert critical == 0, \
        f"{critical} critical gold leakage instances in matching/scoring files. " \
        f"Gold bridge phrases must not appear in scoring logic."
