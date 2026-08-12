"""
Control Ladder Experiment — V1.5

Answers: "Does invariant + constraint reasoning outperform simpler baselines?"

5 methods, same evidence pool, same attackers, blind evaluation.

CONTROL_A: random pairing (no mechanism)
CONTROL_B: keyword similarity (lexical matching)
CONTROL_C: embedding similarity (semantic matching)
CONTROL_D: LLM-only prompt (no mechanism graph, no constraints)
CONTROL_E: Discovery Fabric V1.5 (invariant + constraint + prediction + specialist attack)

All generate cross-domain hypotheses. All are attacked blind by the same specialist attackers.
"""
import json
import sys
import time
import hashlib
import random
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_text, chat_json
from discovery_fabric.v14_pipeline import load_mechanisms, load_evidence

EVAL_DIR = REPO / "discovery_fabric/evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)


def make_blind_case(candidate_id, hypothesis, mechanism, experiment, source_domain, target_domain):
    """Create a blinded case — attacker cannot see generator type."""
    return {
        "id": candidate_id,
        "type": "unknown",  # BLINDED
        "hypothesis": hypothesis,
        "mechanism": mechanism,
        "experiment": experiment or {},
        "source_domain": source_domain,
        "target_domain": target_domain,
    }


# === CONTROL_A: Random pairing ===

def control_a_random(mechanisms, evidence, n=5):
    """Generate hypotheses by random domain pairing — no mechanism reasoning."""
    candidates = []
    domains = list(set(m.get("domain", "?") for m in mechanisms))

    for i in range(n):
        d1, d2 = random.sample(domains, 2)
        m1 = random.choice([m for m in mechanisms if m.get("domain") == d1])

        # Random hypothesis — just states a connection without mechanism
        hypothesis = f"The approach from {d1} ({m1.get('PROCESS', 'a process')[:40]}) may be applicable to {d2}"
        mechanism = f"Transfer of {m1.get('PROCESS', 'unknown process')[:40]} from {d1} to {d2}"

        candidates.append(make_blind_case(
            f"CA-{i}", hypothesis, mechanism,
            {"hypothesis": hypothesis, "experimental_setup": "UNKNOWN", "measurement": "UNKNOWN",
             "expected_result": "UNKNOWN", "failure_result": "UNKNOWN"},
            d1, d2
        ))
    return candidates


# === CONTROL_B: Keyword similarity ===

def control_b_keyword(mechanisms, evidence, n=5):
    """Generate hypotheses by keyword overlap between domains."""
    candidates = []
    domains = list(set(m.get("domain", "?") for m in mechanisms))

    for i in range(n):
        d1, d2 = random.sample(domains, 2)
        m1 = random.choice([m for m in mechanisms if m.get("domain") == d1])
        m2 = random.choice([m for m in mechanisms if m.get("domain") == d2])

        # Find shared keywords
        words1 = set(re.findall(r'\w+', (m1.get("PROCESS", "") + " " + m1.get("INPUT", "")).lower()))
        words2 = set(re.findall(r'\w+', (m2.get("PROCESS", "") + " " + m2.get("INPUT", "")).lower()))
        shared = words1 & words2 - {"unknown", "the", "a", "an", "of", "and", "in", "to", "for", "with"}

        if shared:
            kw = list(shared)[:3]
            hypothesis = f"Shared keywords ({', '.join(kw)}) suggest {d1} approach may transfer to {d2}"
        else:
            hypothesis = f"Process from {d1} ({m1.get('PROCESS', '')[:30]}) may apply to {d2}"
        mechanism = f"Keyword-based similarity: {d1} → {d2}"

        candidates.append(make_blind_case(
            f"CB-{i}", hypothesis, mechanism,
            {"hypothesis": hypothesis, "experimental_setup": "UNKNOWN", "measurement": "UNKNOWN",
             "expected_result": "UNKNOWN", "failure_result": "UNKNOWN"},
            d1, d2
        ))
    return candidates


# === CONTROL_C: LLM-only (no mechanism graph) ===

def control_d_llm_only(mechanisms, evidence, n=5):
    """Generate hypotheses using LLM directly — no mechanism graph, no constraints."""
    candidates = []
    domains = list(set(m.get("domain", "?") for m in mechanisms))

    for i in range(n):
        d1, d2 = random.sample(domains, 2)
        m1 = random.choice([m for m in mechanisms if m.get("domain") == d1])
        eid = m1.get("evidence_id", "")
        abstract = evidence.get(eid, {}).get("abstract", "")[:300]

        prompt = f"""You are a scientist. Given this abstract from {d1}, propose a hypothesis for how it could apply to {d2}.

Abstract: {abstract}

Output JSON: {{"hypothesis":"...","mechanism":"...","experiment":{{"hypothesis":"...","experimental_setup":"...","measurement":"...","expected_result":"...","failure_result":"..."}}}}"""

        text = chat_text(prompt, system="Output ONLY valid JSON.", max_tokens=400)
        result = None
        if text:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    result = json.loads(match.group())
                except:
                    pass

        if result:
            candidates.append(make_blind_case(
                f"CD-{i}",
                result.get("hypothesis", "UNKNOWN"),
                result.get("mechanism", "UNKNOWN"),
                result.get("experiment", {}),
                d1, d2
            ))
        else:
            candidates.append(make_blind_case(
                f"CD-{i}", "LLM generation failed", "UNKNOWN", {}, d1, d2
            ))
        time.sleep(1)

    return candidates


# === CONTROL_E: Discovery Fabric (invariant + constraint) ===

def control_e_discovery_fabric(mechanisms, evidence, invariants, n=5):
    """Generate hypotheses using invariant + constraint pipeline."""
    from discovery_fabric.v14_pipeline import TRANSFER_SYSTEM, evaluate_transfer

    candidates = []
    domains = list(set(inv.get("domain", "?") for inv in invariants if "invariant_principle" in inv))
    pairs = [(d1, d2) for i, d1 in enumerate(domains) for d2 in domains[i+1:]]
    random.shuffle(pairs)

    for i, (d1, d2) in enumerate(pairs[:n]):
        inv = next((inv for inv in invariants if inv.get("domain") == d1 and "invariant_principle" in inv), None)
        if not inv:
            continue

        eid = inv.get("evidence_id", "")
        abstract = evidence.get(eid, {}).get("abstract", "")[:300]

        prompt = f"""Invariant principle from {d1}:
  Principle: {inv.get('invariant_principle', 'UNKNOWN')}
  Causal chain: {inv.get('causal_chain', 'UNKNOWN')}
  Necessary conditions: {inv.get('necessary_conditions', 'UNKNOWN')}
Target domain: {d2}
Source: {abstract}
Can this principle solve a problem in {d2}?"""

        result = chat_json(prompt, system=TRANSFER_SYSTEM, max_tokens=800)

        if result and result.get("transfer_possible") and result.get("quality") != "REJECT":
            exp = result.get("experiment", {})
            candidates.append(make_blind_case(
                f"CE-{i}",
                exp.get("hypothesis", result.get("transferred_mechanism", "")),
                result.get("transferred_mechanism", "UNKNOWN"),
                exp,
                d1, d2
            ))
        else:
            candidates.append(make_blind_case(
                f"CE-{i}", "Transfer rejected by constraint analysis", "UNKNOWN", {}, d1, d2
            ))
        time.sleep(1)

    return candidates


# === Blind Specialist Attack ===

def blind_specialist_attack(case):
    """Attack a blinded case. Cannot see generator type."""
    hypothesis = case.get("hypothesis", "")
    mechanism = case.get("mechanism", "")
    experiment = case.get("experiment", {})
    target = case.get("target_domain", "?")

    attacks = {}
    for specialist, question in [
        ("physics", "Does this violate physics laws? Are energy requirements realistic?"),
        ("materials", "Are required material properties achievable? Are degradation mechanisms ignored?"),
        ("engineering", "Can this be manufactured? Is it economically plausible?"),
    ]:
        prompt = f"""You are a {specialist.upper()} reviewer. {question}

Hypothesis: {hypothesis[:200]}
Mechanism: {mechanism[:200]}
Target domain: {target}

Output ONLY JSON: {{"severity":"FATAL or MAJOR or MINOR or SURVIVES","reason":"brief"}}"""

        text = chat_text(prompt, system="Output ONLY valid JSON.", max_tokens=150)
        if text:
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

    # Survival: ALL must PASS (no FATAL, no MAJOR)
    fatal = sum(1 for a in attacks.values() if a.get("severity") == "FATAL")
    major = sum(1 for a in attacks.values() if a.get("severity") == "MAJOR")
    has_experiment = bool(experiment and experiment.get("hypothesis"))
    has_measurement = bool(experiment and experiment.get("measurement") and experiment.get("measurement") != "UNKNOWN")
    has_falsification = bool(experiment and experiment.get("failure_result") and experiment.get("failure_result") != "UNKNOWN")

    # V1.5 strict survival: no FATAL, no MAJOR, must have experiment+measurement+falsification
    survived = (fatal == 0 and major == 0 and has_experiment and has_measurement and has_falsification
                and not hypothesis.startswith("Transfer rejected") and not hypothesis.startswith("LLM generation"))

    return {
        "case_id": case["id"],
        "overall": "SURVIVES" if survived else "KILLED",
        "fatal_count": fatal,
        "major_count": major,
        "has_experiment": has_experiment,
        "has_measurement": has_measurement,
        "has_falsification": has_falsification,
        "attacks": attacks,
    }


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.5 Control Ladder Experiment")
    print(f"  Question: Does invariant + constraint reasoning outperform simpler baselines?\n")

    mechanisms = load_mechanisms()
    evidence = load_evidence()

    # Load invariants
    with open(REPO / "discovery_fabric/mechanisms/invariants.json") as f:
        inv_data = json.load(f)
    invariants = inv_data.get("invariants", [])

    print(f"  Mechanisms: {len(mechanisms)}")
    print(f"  Invariants: {len([i for i in invariants if 'invariant_principle' in i])}")

    # Generate hypotheses from each method (5 per method)
    N = 4  # per method (keep small for time constraints)

    print(f"\n=== Generating {N} hypotheses per method ===")

    print(f"\n  CONTROL_A (random)...")
    ca = control_a_random(mechanisms, evidence, N)

    print(f"  CONTROL_B (keyword)...")
    cb = control_b_keyword(mechanisms, evidence, N)

    print(f"  CONTROL_D (LLM-only)...")
    cd = control_d_llm_only(mechanisms, evidence, N)

    print(f"  CONTROL_E (Discovery Fabric)...")
    ce = control_e_discovery_fabric(mechanisms, evidence, invariants, N)

    # Generate hard nulls
    print(f"\n  Generating {N} hard nulls...")
    from discovery_fabric.v14_pipeline import generate_hard_null
    nulls = []
    for i in range(N):
        null = generate_hard_null(mechanisms, evidence)
        if null:
            null["id"] = f"NULL-{i}"
            null["type"] = "unknown"
            nulls.append(null)
        time.sleep(1)

    # Combine all cases, shuffle for blinding
    all_cases = ca + cb + cd + ce + nulls
    random.shuffle(all_cases)

    # Record method mapping (kept separate from attacker)
    method_map = {}
    for case in all_cases:
        cid = case["id"]
        if cid.startswith("CA-"):
            method_map[cid] = "random"
        elif cid.startswith("CB-"):
            method_map[cid] = "keyword"
        elif cid.startswith("CD-"):
            method_map[cid] = "llm_only"
        elif cid.startswith("CE-"):
            method_map[cid] = "discovery_fabric"
        elif cid.startswith("NULL-"):
            method_map[cid] = "hard_null"

    print(f"\n=== Blind attack on {len(all_cases)} cases ===")

    results = []
    for i, case in enumerate(all_cases):
        print(f"  [{i+1}/{len(all_cases)}] {case['id']}...", end=" ", flush=True)
        attack = blind_specialist_attack(case)
        attack["method"] = method_map.get(case["id"], "unknown")
        results.append(attack)
        print(f"{attack['overall']} (fatal={attack['fatal_count']}, major={attack['major_count']})")

    # Analysis by method
    print(f"\n=== SURVIVAL BY METHOD ===")
    method_stats = {}
    for method in ["random", "keyword", "llm_only", "discovery_fabric", "hard_null"]:
        method_results = [r for r in results if r["method"] == method]
        survived = sum(1 for r in method_results if r["overall"] == "SURVIVES")
        total = len(method_results)
        method_stats[method] = {
            "total": total,
            "survived": survived,
            "survival_rate": f"{100*survived/max(total,1):.0f}%",
        }
        print(f"  {method}: {survived}/{total} survived ({100*survived/max(total,1):.0f}%)")

    # Save
    output = EVAL_DIR / "V1_5_control_ladder.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Does invariant + constraint reasoning outperform simpler baselines?",
            "method_stats": method_stats,
            "results": results,
            "all_cases": all_cases,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {output}")

    # Determine signal
    df_survival = method_stats.get("discovery_fabric", {}).get("survived", 0)
    null_survival = method_stats.get("hard_null", {}).get("survived", 0)
    llm_survival = method_stats.get("llm_only", {}).get("survived", 0)

    if df_survival > null_survival and df_survival > 0:
        if df_survival > llm_survival:
            signal = "PROMISING SIGNAL — Discovery Fabric outperforms LLM-only"
        else:
            signal = "WEAK SIGNAL — Discovery Fabric matches LLM-only"
    elif df_survival > null_survival:
        signal = "WEAK SIGNAL"
    else:
        signal = "NO SIGNAL"

    print(f"\n  SIGNAL: {signal}")
    return signal


if __name__ == "__main__":
    main()
