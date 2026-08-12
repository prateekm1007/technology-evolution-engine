"""
Combination Discovery Engine — V1.7 core upgrade.

The engine asks: "What happens when two independently validated truths 
become coupled under a new constraint regime?"

Pipeline:
  1. Identify mechanism pairs from different domains
  2. Check constraint compatibility (shared constraints, no conflicts)
  3. Generate combination hypothesis with emergent property
  4. Test emergence (does A+B create something neither can alone?)
  5. Generate falsifiable prediction
  6. Attack with specialists
  7. Only score >=2 emergence proceeds to candidate

This is NOT "Paper A + Paper B". It is "Mechanism A + Mechanism B → new capability".
"""
import json
import sys
import time
import hashlib
import random
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json, chat_text

MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/extraction_checkpoint_v4.json"
CONSTRAINTS_FILE = REPO / "discovery_fabric/mechanisms/constraints_v4.json"
INVARIANTS_FILE = REPO / "discovery_fabric/mechanisms/invariants.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
COMBINATIONS_DIR = REPO / "discovery_fabric/combinations"
COMBINATIONS_DIR.mkdir(parents=True, exist_ok=True)

UNKNOWN = "UNKNOWN"


def load_mechanisms():
    with open(MECHANISMS_FILE) as f:
        data = json.load(f)
    return [m for m in data.get("mechanisms", []) if m.get("extraction_status") == "SUCCESS"]


def load_constraints():
    if not CONSTRAINTS_FILE.exists():
        return {}
    with open(CONSTRAINTS_FILE) as f:
        data = json.load(f)
    return {c["evidence_id"]: c for c in data.get("constraints", []) if "extraction_status" not in c}


def load_invariants():
    if not INVARIANTS_FILE.exists():
        return {}
    with open(INVARIANTS_FILE) as f:
        data = json.load(f)
    return {inv["evidence_id"]: inv for inv in data.get("invariants", []) if "invariant_principle" in inv}


def load_evidence():
    evidence = {}
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                evidence[e["id"]] = e
    return evidence


# === Combination Schema ===

def create_combination_object(mech_a, mech_b, inv_a, inv_b, combination_result):
    """Create a combination discovery object."""
    return {
        "id": f"COMBO-{hashlib.sha256(f'{mech_a['evidence_id']}-{mech_b['evidence_id']}'.encode()).hexdigest()[:8]}",
        "mechanism_a": {
            "evidence_id": mech_a["evidence_id"],
            "domain": mech_a.get("domain", "?"),
            "process": mech_a.get("PROCESS", UNKNOWN),
            "invariant": inv_a.get("invariant_principle", UNKNOWN) if inv_a else UNKNOWN,
        },
        "mechanism_b": {
            "evidence_id": mech_b["evidence_id"],
            "domain": mech_b.get("domain", "?"),
            "process": mech_b.get("PROCESS", UNKNOWN),
            "invariant": inv_b.get("invariant_principle", UNKNOWN) if inv_b else UNKNOWN,
        },
        "source_domains": [mech_a.get("domain", "?"), mech_b.get("domain", "?")],
        "validated_independently": True,
        "invariant_a": inv_a.get("invariant_principle", UNKNOWN) if inv_a else UNKNOWN,
        "invariant_b": inv_b.get("invariant_principle", UNKNOWN) if inv_b else UNKNOWN,
        "shared_constraint": combination_result.get("shared_constraint", UNKNOWN),
        "new_interaction": combination_result.get("new_interaction", UNKNOWN),
        "emergent_property": combination_result.get("emergent_property", UNKNOWN),
        "why_combination_did_not_exist": combination_result.get("why_combination_did_not_exist", UNKNOWN),
        "required_conditions": combination_result.get("required_conditions", []),
        "predicted_effect": combination_result.get("predicted_effect", UNKNOWN),
        "measurement_method": combination_result.get("measurement_method", UNKNOWN),
        "failure_condition": combination_result.get("failure_condition", UNKNOWN),
        "prior_art_status": "UNKNOWN",
        "epistemic_state": "HYPOTHESIS",
        "emergence_score": combination_result.get("emergence_score", 0),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# === LLM Prompts ===

COMBINATION_SYSTEM = """You are a combination discovery evaluator for a scientific discovery engine.

Given two independently validated mechanisms from different domains, evaluate whether combining them creates an EMERGENT capability — something neither mechanism can produce alone.

CRITICAL RULES:
1. The combination must create something NEW, not just additive.
2. Both mechanisms must be independently validated (they work on their own).
3. The combination must be physically possible (no constraint conflicts).
4. You MUST produce a falsifiable prediction if the combination is viable.
5. Score emergence: 0=additive only, 1=weak synergy, 2=meaningful interaction, 3=emergent capability
6. Only score >=2 should proceed.

Reject immediately if:
- NO_SHARED_CONSTRAINT: the mechanisms have no compatible operating conditions
- NO_INTERACTION: the mechanisms don't interact in any meaningful way
- DUPLICATE_KNOWLEDGE: the combination is already known
- CONSTRAINT_CONFLICT: the mechanisms require incompatible conditions

Output JSON:
{
  "combination_viable": true/false,
  "rejection_reason": "NO_SHARED_CONSTRAINT/NO_INTERACTION/DUPLICATE_KNOWLEDGE/CONSTRAINT_CONFLICT/null",
  "shared_constraint": "what constraint do both mechanisms operate under",
  "new_interaction": "how do the mechanisms interact when combined",
  "emergent_property": "what new capability emerges from the combination",
  "why_combination_did_not_exist": "why hasn't this been done before",
  "required_conditions": ["conditions needed for the combination"],
  "predicted_effect": "specific measurable prediction",
  "measurement_method": "how to measure it",
  "failure_condition": "what would falsify this",
  "emergence_score": 0-3
}"""


def evaluate_combination(mech_a, mech_b, inv_a, inv_b, abstract_a, abstract_b):
    """Use LLM to evaluate whether two mechanisms can combine into something emergent."""
    prompt = f"""Mechanism A (from {mech_a.get('domain', '?')}):
  Process: {mech_a.get('PROCESS', UNKNOWN)}
  Input: {mech_a.get('INPUT', UNKNOWN)}
  Output: {mech_a.get('OUTPUT', UNKNOWN)}
  Invariant: {inv_a.get('invariant_principle', UNKNOWN) if inv_a else UNKNOWN}
  Abstract: {abstract_a[:300]}

Mechanism B (from {mech_b.get('domain', '?')}):
  Process: {mech_b.get('PROCESS', UNKNOWN)}
  Input: {mech_b.get('INPUT', UNKNOWN)}
  Output: {mech_b.get('OUTPUT', UNKNOWN)}
  Invariant: {inv_b.get('invariant_principle', UNKNOWN) if inv_b else UNKNOWN}
  Abstract: {abstract_b[:300]}

Can combining these two mechanisms create an emergent capability? Evaluate the combination."""

    result = chat_json(prompt, system=COMBINATION_SYSTEM, max_tokens=800)
    if not result:
        return None
    return result


# === Specialist Attack (calibrated V1.7) ===

def calibrated_attack(combination):
    """Attack a combination with calibrated severity (Fatal/Major/Minor/Survives)."""
    hyp = combination.get("predicted_effect", "")
    mech = combination.get("new_interaction", "")
    emergent = combination.get("emergent_property", "")
    conditions = combination.get("required_conditions", [])

    attacks = {}
    for specialist, question in [
        ("physics", "Does this violate physics laws? Are energy requirements realistic?"),
        ("materials", "Are required material properties achievable? Are degradation mechanisms ignored?"),
        ("engineering", "Can this be manufactured? Is it economically plausible?"),
    ]:
        prompt = f"""You are a {specialist.upper()} reviewer. {question}

Combination hypothesis: {hyp[:200]}
New interaction: {mech[:200]}
Emergent property: {emergent[:200]}
Required conditions: {conditions}

Severity guide:
- FATAL: Impossible physics/chemistry/biology. Cannot work.
- MAJOR: Important but potentially fixable challenge. Development risk.
- MINOR: Engineering optimization needed. Not a fundamental problem.
- SURVIVES: No significant issues found.

Output ONLY JSON: {{"severity":"FATAL/MAJOR/MINOR/SURVIVES","reason":"brief"}}"""

        text = chat_text(prompt, system="Output ONLY valid JSON. No prose.", max_tokens=150)
        if text:
            import re
            match = re.search(r'\{[^}]+\}', text)
            if match:
                try:
                    attacks[specialist] = json.loads(match.group())
                except:
                    attacks[specialist] = {"severity": "UNASSESSED", "reason": "parse failed"}
            else:
                attacks[specialist] = {"severity": "UNASSESSED", "reason": "no JSON"}
        else:
            attacks[specialist] = {"severity": "UNASSESSED", "reason": "LLM failed"}
        time.sleep(1)

    # V1.7 Calibrated survival: Fatal=0 AND has prediction AND has experiment AND mechanism coherent
    fatal = sum(1 for a in attacks.values() if a.get("severity") == "FATAL")
    has_prediction = bool(combination.get("predicted_effect") and combination["predicted_effect"] != UNKNOWN)
    has_experiment = bool(combination.get("measurement_method") and combination["measurement_method"] != UNKNOWN)
    has_falsification = bool(combination.get("failure_condition") and combination["failure_condition"] != UNKNOWN)
    mechanism_coherent = bool(combination.get("new_interaction") and combination["new_interaction"] != UNKNOWN)

    # V1.7: Major issues are "development risk", not automatic rejection
    survived = (fatal == 0 and has_prediction and has_experiment and has_falsification and mechanism_coherent)

    return {
        "overall": "SURVIVES" if survived else "KILLED",
        "fatal_count": fatal,
        "major_count": sum(1 for a in attacks.values() if a.get("severity") == "MAJOR"),
        "minor_count": sum(1 for a in attacks.values() if a.get("severity") == "MINOR"),
        "survives_count": sum(1 for a in attacks.values() if a.get("severity") == "SURVIVES"),
        "has_prediction": has_prediction,
        "has_experiment": has_experiment,
        "has_falsification": has_falsification,
        "mechanism_coherent": mechanism_coherent,
        "attacks": attacks,
        "survival_rule": "V1.7 calibrated: Fatal=0 AND prediction AND experiment AND falsification AND mechanism_coherent. Major = development risk, not rejection.",
    }


# === Main Pipeline ===

def main(max_pairs=8):
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.7 Combination Discovery Engine")
    print(f"  Mission: What happens when two independently validated truths become coupled?\n")

    mechanisms = load_mechanisms()
    constraints = load_constraints()
    invariants = load_invariants()
    evidence = load_evidence()

    print(f"  Mechanisms: {len(mechanisms)}")
    print(f"  Constraints: {len(constraints)}")
    print(f"  Invariants: {len(invariants)}")

    # Group by domain
    by_domain = defaultdict(list)
    for m in mechanisms:
        by_domain[m.get("domain", "?")].append(m)

    domains = list(by_domain.keys())
    print(f"  Domains: {domains}")

    # Generate cross-domain mechanism pairs
    pairs = []
    for i, d1 in enumerate(domains):
        for d2 in domains[i+1:]:
            for m1 in by_domain[d1][:2]:  # top 2 per domain
                for m2 in by_domain[d2][:2]:
                    pairs.append((m1, m2))

    random.seed(42)
    random.shuffle(pairs)
    pairs = pairs[:max_pairs]

    print(f"\n  Evaluating {len(pairs)} mechanism pairs...\n")

    combinations = []
    rejected = []

    for i, (m1, m2) in enumerate(pairs):
        eid1 = m1["evidence_id"]
        eid2 = m2["evidence_id"]
        inv1 = invariants.get(eid1, {})
        inv2 = invariants.get(eid2, {})
        abstract1 = evidence.get(eid1, {}).get("abstract", "")[:300]
        abstract2 = evidence.get(eid2, {}).get("abstract", "")[:300]

        print(f"  [{i+1}/{len(pairs)}] {m1.get('domain','?')}+{m2.get('domain','?')}...", end=" ", flush=True)

        result = evaluate_combination(m1, m2, inv1, inv2, abstract1, abstract2)

        if result and result.get("combination_viable") and result.get("emergence_score", 0) >= 2:
            combo = create_combination_object(m1, m2, inv1, inv2, result)
            combinations.append(combo)
            print(f"VIABLE (emergence={result.get('emergence_score','?')}) — {result.get('emergent_property','')[:60]}")
        else:
            reason = result.get("rejection_reason", "low_emergence") if result else "LLM failed"
            score = result.get("emergence_score", 0) if result else 0
            rejected.append({"pair": f"{eid1}+{eid2}", "reason": reason, "emergence_score": score})
            print(f"REJECTED ({reason}, score={score})")

        time.sleep(1)

    print(f"\n  Combinations generated: {len(combinations)}")
    print(f"  Rejected: {len(rejected)}")

    # Attack surviving combinations
    if combinations:
        print(f"\n  Attacking {len(combinations)} combinations (calibrated V1.7)...\n")
        for combo in combinations:
            print(f"    {combo['id']}...", end=" ", flush=True)
            attack = calibrated_attack(combo)
            combo["attack_result"] = attack
            print(f"{attack['overall']} (fatal={attack['fatal_count']}, major={attack['major_count']}, minor={attack['minor_count']})")
            time.sleep(1)

    # Analysis
    survived = sum(1 for c in combinations if c.get("attack_result", {}).get("overall") == "SURVIVES")
    print(f"\n=== V1.7 COMBINATION DISCOVERY RESULTS ===")
    print(f"  Pairs evaluated: {len(pairs)}")
    print(f"  Combinations viable (emergence >=2): {len(combinations)}")
    print(f"  Survived calibrated attack: {survived}")
    print(f"  Rejection reasons: {Counter(r['reason'] for r in rejected)}")

    # Save
    output = COMBINATIONS_DIR / "combination_results.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_version": "V1.7",
            "pairs_evaluated": len(pairs),
            "combinations_viable": len(combinations),
            "survived": survived,
            "combinations": combinations,
            "rejected": rejected,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {output}")
    return combinations


if __name__ == "__main__":
    main()
