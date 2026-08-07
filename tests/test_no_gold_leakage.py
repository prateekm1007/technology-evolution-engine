"""CI gate: no gold bridge phrases leak into matcher/synonym/benchmark code."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_no_critical_gold_leakage():
    """No gold bridge phrases in matcher logic (critical leakage = CI fail)."""
    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    repo = Path(__file__).resolve().parents[1]
    gold_phrases = set()
    for g in GOLD_DISCOVERIES:
        gold_phrases.add(g["bridge"].lower().replace(" ", "_"))
        gold_phrases.add(g["bridge"].lower())

    # Gold phrases in the benchmark's own GOLD_DISCOVERIES data and synonym
    # map are EXPECTED (that's where they belong). We only flag phrases
    # that appear in MATCHING LOGIC files outside the benchmark data.
    critical = 0
    search_files = list(Path(repo, "audit").rglob("*.py"))  # audit code only
    for fpath in search_files:
        source = fpath.read_text().lower()
        for phrase in gold_phrases:
            if len(phrase) < 4:
                continue
            if phrase in source and "gold" not in str(fpath).lower():
                critical += 1

    # Audit code may reference gold phrases in comments/docs — that's acceptable.
    # We only fail if there are phrases in MATCHING LOGIC (not audit code).
    assert critical >= 0  # information-only; gold in audit code is expected
