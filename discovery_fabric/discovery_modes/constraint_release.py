"""
Constraint Release Detection — discovers opportunities where a blocked
mechanism becomes possible because a new enabling technology removes a constraint.

Pattern: old_constraint + new_enabling_factor = mechanism_unlocked
"""
import json
import sys
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

RELEASE_SYSTEM = """You are a constraint release analyst for a scientific discovery engine.

Your job: Identify cases where a previously blocked mechanism becomes possible because a new enabling technology removes a constraint.

Pattern:
  OLD CONSTRAINT: What was preventing this mechanism from working?
  PREVIOUS FAILURE MODE: How did it fail before?
  NEW ENABLING FACTOR: What new technology/approach removes the constraint?
  MECHANISM UNLOCKED: What becomes possible now?

CRITICAL RULES:
1. The constraint must have been REAL.
2. The enabling factor must be NEW.
3. Must produce a MEASURABLE, FALSIFIABLE prediction.

Output JSON:
{
  "constraint_release_viable": true/false,
  "old_constraint": "",
  "previous_failure_mode": "",
  "new_enabling_factor": "",
  "mechanism_unlocked": "",
  "predicted_effect": "",
  "experiment": "",
  "falsification": "",
  "historical_parallel": "",
  "confidence": 0.0
}"""


def detect_constraint_release(mech_a, mech_b, abstract_a, abstract_b):
    prompt = f"""Mechanism A:
  Process: {mech_a.get('PROCESS', 'UNKNOWN')}
  Failure mode: {mech_a.get('FAILURE_MODE', 'UNKNOWN')}
  Constraints: {mech_a.get('CONSTRAINTS', 'UNKNOWN')}
  Abstract: {abstract_a[:250]}

Mechanism B (potential enabler):
  Process: {mech_b.get('PROCESS', 'UNKNOWN')}
  Output: {mech_b.get('OUTPUT', 'UNKNOWN')}
  Abstract: {abstract_b[:250]}

Does Mechanism B remove a constraint blocking Mechanism A?"""

    return chat_json(prompt, system=RELEASE_SYSTEM, max_tokens=700)


def run_analysis(mechanisms, evidence, max_pairs=5):
    from collections import defaultdict
    import random
    random.seed(99)

    by_domain = defaultdict(list)
    for m in mechanisms:
        by_domain[m.get("domain", "?")].append(m)

    domains = list(by_domain.keys())
    pairs = []
    for i, d1 in enumerate(domains):
        for d2 in domains[i+1:]:
            for m1 in by_domain[d1][:1]:
                for m2 in by_domain[d2][:1]:
                    pairs.append((m1, m2))
    random.shuffle(pairs)

    releases = []
    for i, (m1, m2) in enumerate(pairs[:max_pairs]):
        eid1, eid2 = m1["evidence_id"], m2["evidence_id"]
        a1 = evidence.get(eid1, {}).get("abstract", "")[:250]
        a2 = evidence.get(eid2, {}).get("abstract", "")[:250]

        print(f"    [{i+1}] {m1.get('domain','?')}+{m2.get('domain','?')}...", end=" ", flush=True)
        result = detect_constraint_release(m1, m2, a1, a2)

        if result and result.get("constraint_release_viable"):
            release = {
                "id": f"CR-{hashlib.sha256(f'{eid1}-{eid2}'.encode()).hexdigest()[:8]}",
                "old_constraint": result.get("old_constraint", "UNKNOWN"),
                "previous_failure_mode": result.get("previous_failure_mode", "UNKNOWN"),
                "new_enabling_factor": result.get("new_enabling_factor", "UNKNOWN"),
                "mechanism_unlocked": result.get("mechanism_unlocked", "UNKNOWN"),
                "predicted_effect": result.get("predicted_effect", "UNKNOWN"),
                "experiment": result.get("experiment", "UNKNOWN"),
                "falsification": result.get("falsification", "UNKNOWN"),
                "historical_parallel": result.get("historical_parallel", "UNKNOWN"),
                "confidence": result.get("confidence", 0),
            }
            releases.append(release)
            print(f"RELEASE — {result.get('mechanism_unlocked','')[:50]}")
        else:
            print("NONE")
        time.sleep(1)

    return releases
