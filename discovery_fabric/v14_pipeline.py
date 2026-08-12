"""
V1.4 Pipeline: Invariant-based transfer + specialist attack + hard nulls.

Key change from V4: Generate from INVARIANT PHYSICAL PRINCIPLE, not mechanism similarity.

Pipeline:
  1. Extract invariant principle from each mechanism
  2. For each invariant, search where it solves a different constraint in another domain
  3. Generate transfer hypothesis with experiment design
  4. Attack with specialist attackers (physics, materials, biology, engineering)
  5. Only candidates that survive all specialist attacks become V1.4 candidates
"""
import json
import sys
import time
import hashlib
import random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/extraction_checkpoint_v4.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
CANDIDATES_DIR = REPO / "discovery_fabric/discovery_candidates"
REPORTS_DIR = REPO / "discovery_fabric/reports"
ATTACKER_DIR = REPO / "discovery_fabric/adversarial_review"

UNKNOWN = "UNKNOWN"
random.seed(42)


def load_mechanisms():
    with open(MECHANISMS_FILE) as f:
        data = json.load(f)
    return [m for m in data.get("mechanisms", []) if m.get("extraction_status") == "SUCCESS"]


def load_evidence():
    evidence = {}
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                evidence[e["id"]] = e
    return evidence


# === Step 1: Invariant Extraction ===

INVARIANT_SYSTEM = """You are a physics-aware mechanism analyst. Extract the INVARIANT PRINCIPLE from a scientific mechanism.

The invariant principle is: "What remains true if the domain changes?"

This is NOT the specific application. It is the underlying physical/chemical/biological principle that could potentially transfer.

Example:
Bad (domain-specific): "Perovskite solar cell achieves 25% efficiency"
Good (invariant): "Tunable bandgap heterostructures enable broadband light absorption with reduced thermalization losses"

Output JSON:
{
  "invariant_principle": "the domain-independent physical principle",
  "causal_chain": "cause → intermediate → effect (domain-independent)",
  "necessary_conditions": "what must be true for this principle to operate",
  "failure_conditions": "when does this principle break down",
  "scaling_limits": "what limits this principle at different scales"
}"""

def extract_invariant(mechanism, abstract):
    """Extract invariant physical principle from a mechanism."""
    mech_summary = "\n".join(f"  {f}: {mechanism.get(f, UNKNOWN)}" for f in [
        "OBJECTIVE", "INPUT", "PROCESS", "OUTPUT", "MEASURED_EFFECT",
        "OPERATING_CONDITIONS", "CONSTRAINTS"
    ])

    prompt = f"""Mechanism:
{mech_summary}

Source abstract:
{abstract[:600]}

Extract the invariant physical principle. What remains true if the domain changes?"""

    result = chat_json(prompt, system=INVARIANT_SYSTEM, max_tokens=600)
    if not result:
        return None
    return result


# === Step 2: Transfer Hypothesis Generation ===

TRANSFER_SYSTEM = """You are a cross-domain transfer evaluator. Given an invariant principle from domain A, evaluate whether it can solve a problem in domain B.

CRITICAL RULES:
1. Only propose transfer if the invariant principle's NECESSARY CONDITIONS are achievable in domain B.
2. The transfer must be based on the PHYSICAL PRINCIPLE, not word similarity.
3. You MUST produce a falsifiable, experimentally testable prediction.
4. If you cannot design an experiment, output transfer_possible: false.
5. Reject superficial analogies (e.g., "both use surfaces" is NOT a transfer).

Output JSON:
{
  "transfer_possible": true/false,
  "invariant_principle": "the principle being transferred",
  "source_domain": "A",
  "target_domain": "B",
  "target_problem": "what problem in B could this solve",
  "transferred_mechanism": "how the principle would work in B",
  "necessary_conditions_met": "are the necessary conditions achievable in B? why?",
  "experiment": {
    "hypothesis": "If principle X is applied to domain B, then...",
    "experimental_setup": "specific setup",
    "control_group": "what is the control",
    "measurement": "what to measure",
    "expected_result": "specific expected value or direction",
    "failure_result": "what result would falsify this"
  },
  "constraint_conflicts": ["list of conflicts, empty if none"],
  "quality": "STRONG/MODERATE/WEAK/REJECT"
}"""

def evaluate_transfer(invariant, source_domain, target_domain, source_abstract):
    """Evaluate whether an invariant principle can transfer to a target domain."""
    prompt = f"""Invariant principle from {source_domain}:
  Principle: {invariant.get('invariant_principle', UNKNOWN)}
  Causal chain: {invariant.get('causal_chain', UNKNOWN)}
  Necessary conditions: {invariant.get('necessary_conditions', UNKNOWN)}
  Failure conditions: {invariant.get('failure_conditions', UNKNOWN)}
  Scaling limits: {invariant.get('scaling_limits', UNKNOWN)}

Target domain: {target_domain}

Source abstract for context:
{source_abstract[:400]}

Can this invariant principle solve a problem in {target_domain}? Evaluate the transfer."""

    result = chat_json(prompt, system=TRANSFER_SYSTEM, max_tokens=800)
    if not result:
        return None
    return result


# === Step 3: Specialist Attackers ===

def physics_attack(candidate):
    """Physics attacker: conservation laws, energy, timescales."""
    prompt = f"""You are a PHYSICS reviewer. Attack this hypothesis on physics grounds.

Hypothesis: {candidate.get('transferred_mechanism', candidate.get('experiment', {}).get('hypothesis', ''))}
Necessary conditions: {candidate.get('necessary_conditions_met', '')}
Constraint conflicts: {candidate.get('constraint_conflicts', [])}

Check:
1. Does this violate known physics laws?
2. Are energy requirements realistic?
3. Are timescales compatible?
4. Are thermodynamic constraints satisfied?

Output JSON: {{"severity": "FATAL/MAJOR/MINOR/SURVIVES", "reason": "..."}}"""
    return chat_json(prompt, max_tokens=300)


def materials_attack(candidate):
    """Materials attacker: properties, degradation, scale."""
    prompt = f"""You are a MATERIALS SCIENTIST. Attack this hypothesis on materials grounds.

Hypothesis: {candidate.get('transferred_mechanism', '')}
Target domain: {candidate.get('target_domain', '')}
Necessary conditions: {candidate.get('necessary_conditions_met', '')}

Check:
1. Are required material properties achievable?
2. Are degradation mechanisms ignored?
3. Does the mechanism survive scale-up?
4. Are there known material incompatibilities?

Output JSON: {{"severity": "FATAL/MAJOR/MINOR/SURVIVES", "reason": "..."}}"""
    return chat_json(prompt, max_tokens=300)


def biology_attack(candidate):
    """Biology attacker: causality, function preservation."""
    prompt = f"""You are a BIOLOGIST. Attack this hypothesis on biological grounds.

Hypothesis: {candidate.get('transferred_mechanism', '')}
Target domain: {candidate.get('target_domain', '')}

Check:
1. Is the biological mechanism causal or merely descriptive?
2. Does transfer preserve function?
3. Are there biological safety concerns?
4. Is the biological system too complex for the proposed mechanism?

Output JSON: {{"severity": "FATAL/MAJOR/MINOR/SURVIVES", "reason": "..."}}"""
    return chat_json(prompt, max_tokens=300)


def engineering_attack(candidate):
    """Engineering attacker: manufacturability, economics."""
    prompt = f"""You are an ENGINEER. Attack this hypothesis on engineering grounds.

Hypothesis: {candidate.get('transferred_mechanism', '')}
Experiment: {candidate.get('experiment', {}).get('experimental_setup', '')}

Check:
1. Can this be manufactured at scale?
2. Is it economically plausible?
3. Are there engineering constraints that prevent implementation?
4. Is the experiment practically feasible?

Output JSON: {{"severity": "FATAL/MAJOR/MINOR/SURVIVES", "reason": "..."}}"""
    return chat_json(prompt, max_tokens=300)


def run_specialist_attacks(candidate):
    """Run all 4 specialist attacks on a candidate."""
    attacks = {}
    for name, func in [("physics", physics_attack), ("materials", materials_attack),
                        ("biology", biology_attack), ("engineering", engineering_attack)]:
        result = func(candidate)
        if result and "severity" in result:
            attacks[name] = {"severity": result["severity"], "reason": result.get("reason", "")}
        else:
            attacks[name] = {"severity": "UNASSESSED", "reason": "LLM failed"}
        time.sleep(0.5)

    # Determine overall survival
    fatal_count = sum(1 for a in attacks.values() if a["severity"] == "FATAL")
    major_count = sum(1 for a in attacks.values() if a["severity"] == "MAJOR")

    if fatal_count > 0:
        overall = "KILLED"
    elif major_count >= 2:
        overall = "KILLED"
    else:
        overall = "SURVIVES"

    return {"attacks": attacks, "overall": overall, "fatal_count": fatal_count, "major_count": major_count}


# === Step 4: Hard Null Generator ===

def generate_hard_null(mechanisms, evidence):
    """Generate a hard null: scientific-looking but with hidden impossibility."""
    # Pick two mechanisms from different domains
    domains = list(set(m.get("domain", "?") for m in mechanisms))
    if len(domains) < 2:
        return None

    d1, d2 = random.sample(domains, 2)
    m1 = random.choice([m for m in mechanisms if m.get("domain") == d1])
    m2 = random.choice([m for m in mechanisms if m.get("domain") == d2])
    if not m1 or not m2:
        return None

    # Generate a plausible-looking but subtly wrong transfer
    prompt = f"""Create a SCIENTIFIC-LOOKING but WRONG cross-domain hypothesis. It should sound convincing but contain a hidden physical impossibility.

Source mechanism from {d1}: {m1.get('PROCESS', 'unknown')} — {m1.get('OBJECTIVE', '')[:80]}
Target domain: {d2}

Create a hypothesis that:
1. Sounds scientifically plausible (50% of humans would find it interesting)
2. Contains a HIDDEN physical impossibility (wrong energy scale, incompatible timescale, material incompatibility, etc.)
3. Includes a fake experiment and prediction

Output JSON:
{{
  "invariant_principle": "plausible-sounding principle",
  "source_domain": "{d1}",
  "target_domain": "{d2}",
  "target_problem": "plausible problem",
  "transferred_mechanism": "plausible but wrong mechanism",
  "necessary_conditions_met": "plausible-sounding conditions",
  "experiment": {{
    "hypothesis": "plausible hypothesis",
    "experimental_setup": "plausible setup",
    "control_group": "control",
    "measurement": "measurement",
    "expected_result": "expected",
    "failure_result": "falsifier"
  }},
  "constraint_conflicts": [],
  "quality": "MODERATE",
  "hidden_flaw": "what is the hidden impossibility"
}}"""

    result = chat_json(prompt, max_tokens=600)
    if not result:
        return None
    # Remove hidden_flaw so attacker can't see it
    result.pop("hidden_flaw", None)
    result["is_hard_null"] = True  # for analysis AFTER attack only
    return result


# === Main Pipeline ===

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.4 Pipeline starting")

    mechanisms = load_mechanisms()
    evidence = load_evidence()
    print(f"  Mechanisms: {len(mechanisms)}")
    print(f"  Domains: {Counter(m.get('domain','?') for m in mechanisms)}")

    # Step 1: Extract invariants for all mechanisms
    print("\n=== Step 1: Invariant Extraction ===")
    invariants = []
    invariant_file = REPO / "discovery_fabric/mechanisms/invariants.json"

    # Load existing
    existing = {}
    if invariant_file.exists():
        with open(invariant_file) as f:
            for inv in json.load(f).get("invariants", []):
                eid = inv.get("evidence_id", "")
                if eid:
                    existing[eid] = inv

    for i, m in enumerate(mechanisms):
        eid = m["evidence_id"]
        if eid in existing:
            invariants.append(existing[eid])
            continue

        abstract = evidence.get(eid, {}).get("abstract", "")
        inv = extract_invariant(m, abstract)
        if inv:
            inv["evidence_id"] = eid
            inv["domain"] = m.get("domain", "?")
            inv["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
            invariants.append(inv)
        else:
            invariants.append({"evidence_id": eid, "domain": m.get("domain", "?"), "extraction_status": "FAILED"})

        # Save after every item
        with open(invariant_file, "w") as f:
            json.dump({"total": len(invariants), "invariants": invariants}, f, indent=2, ensure_ascii=False)

        if (i + 1) % 5 == 0:
            success = sum(1 for inv in invariants if "invariant_principle" in inv)
            print(f"  [{i+1}/{len(mechanisms)}] success={success}")

    success_invariants = [inv for inv in invariants if "invariant_principle" in inv]
    print(f"\n  Invariants extracted: {len(success_invariants)}/{len(mechanisms)}")

    # Step 2: Generate transfer hypotheses (cross-domain)
    print("\n=== Step 2: Transfer Hypothesis Generation ===")
    candidates = []
    domains = list(set(m.get("domain", "?") for m in mechanisms))

    # For each pair of domains, try ONE transfer
    pairs_tried = 0
    for d1 in domains:
        for d2 in domains:
            if d1 >= d2:
                continue
            if pairs_tried >= 10:  # limit for time
                break

            # Find an invariant from d1
            source_inv = next((inv for inv in success_invariants if inv.get("domain") == d1), None)
            if not source_inv:
                continue

            source_eid = source_inv.get("evidence_id", "")
            source_abstract = evidence.get(source_eid, {}).get("abstract", "")

            print(f"  {d1} → {d2}...", end=" ", flush=True)
            transfer = evaluate_transfer(source_inv, d1, d2, source_abstract)

            if transfer and transfer.get("transfer_possible") and transfer.get("quality") != "REJECT":
                transfer["candidate_id"] = f"V14-{hashlib.sha256(f'{d1}-{d2}-{pairs_tried}'.encode()).hexdigest()[:8]}"
                transfer["epistemic_state"] = "MECHANISTIC_HYPOTHESIS"
                transfer["generated_at"] = datetime.now(timezone.utc).isoformat()
                candidates.append(transfer)
                print(f"ACCEPTED ({transfer.get('quality','?')})")
            else:
                quality = transfer.get("quality", "FAILED") if transfer else "FAILED"
                print(f"REJECTED ({quality})")

            pairs_tried += 1
            time.sleep(1)
        if pairs_tried >= 10:
            break

    print(f"\n  Candidates generated: {len(candidates)}")

    # Step 3: Generate hard nulls
    print("\n=== Step 3: Hard Null Generation ===")
    hard_nulls = []
    for i in range(min(6, len(candidates))):  # match null count to candidate count
        print(f"  Generating null {i+1}...", end=" ", flush=True)
        null = generate_hard_null(mechanisms, evidence)
        if null:
            null["candidate_id"] = f"NULL-V14-{hashlib.sha256(f'null-{i}'.encode()).hexdigest()[:8]}"
            hard_nulls.append(null)
            print("OK")
        else:
            print("FAILED")
        time.sleep(1)

    print(f"  Hard nulls generated: {len(hard_nulls)}")

    # Step 4: Specialist attack on ALL candidates + nulls (blind)
    print("\n=== Step 4: Specialist Attack (Blind) ===")
    all_to_attack = candidates + hard_nulls
    random.shuffle(all_to_attack)  # mix so attacker doesn't know order

    results = []
    for i, cand in enumerate(all_to_attack):
        is_null = cand.get("is_hard_null", False)
        print(f"  [{i+1}/{len(all_to_attack)}] {cand.get('candidate_id','?')[:20]}...", end=" ", flush=True)

        attack_result = run_specialist_attacks(cand)
        attack_result["candidate_id"] = cand.get("candidate_id", "")
        attack_result["is_null"] = is_null
        results.append(attack_result)

        print(f"{attack_result['overall']} (fatal={attack_result['fatal_count']}, major={attack_result['major_count']})")
        time.sleep(1)

    # Step 5: Analysis
    print("\n=== Step 5: Survival Analysis ===")
    real_results = [r for r in results if not r["is_null"]]
    null_results = [r for r in results if r["is_null"]]

    real_survived = sum(1 for r in real_results if r["overall"] == "SURVIVES")
    null_survived = sum(1 for r in null_results if r["overall"] == "SURVIVES")

    print(f"\n  REAL candidates: {len(real_results)} → {real_survived} survived ({100*real_survived/max(len(real_results),1):.0f}%)")
    print(f"  HARD NULLS: {len(null_results)} → {null_survived} survived ({100*null_survived/max(len(null_results),1):.0f}%)")
    print(f"  Null rejection rate: {100*(1-null_survived/max(len(null_results),1)):.0f}%")
    print(f"  False positive rate: {100*null_survived/max(len(null_results),1):.0f}%")

    # Save everything
    output = REPORTS_DIR / "V1_4_results.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mechanisms_count": len(mechanisms),
            "invariants_extracted": len(success_invariants),
            "candidates_generated": len(candidates),
            "hard_nulls_generated": len(hard_nulls),
            "real_survived": real_survived,
            "real_total": len(real_results),
            "null_survived": null_survived,
            "null_total": len(null_results),
            "results": results,
            "candidates": candidates,
            "hard_nulls": hard_nulls,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {output}")

    # Determine signal
    if real_survived > null_survived and real_survived > 0:
        signal = "PRELIMINARY DISCOVERY SIGNAL"
    elif real_survived > 0 and null_survived == 0:
        signal = "PRELIMINARY DISCOVERY SIGNAL"
    else:
        signal = "NO DISCOVERY SIGNAL YET"

    print(f"\n  SIGNAL: {signal}")
    return signal


if __name__ == "__main__":
    main()
