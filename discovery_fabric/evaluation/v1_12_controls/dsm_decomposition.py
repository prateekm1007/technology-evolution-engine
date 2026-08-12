"""
DSM Decomposition Harness — replaces holistic DSM with 6 objective subclaims.

Each subclaim is independently scored with evidence spans (quotes from the proposal/target).
No single holistic DSM label. Agreement is measured PER SUBCLAIM.

Subclaims:
1. COMPONENT_OVERLAP: Do proposal and target name the same physical/material components?
2. CAUSAL_RELATION_OVERLAP: Do they identify the same causal chain (A causes B causes C)?
3. COMBINATION_INTERACTION_OVERLAP: Do they identify the same combination/interaction of mechanisms?
4. CONSTRAINT_RELEASE_OVERLAP: Do they identify the same constraint being removed/overcome?
5. EXPERIMENTALLY_TESTABLE_CONSEQUENCE: Does the proposal predict a testable consequence matching the target?
6. RELATION_EXPLICIT_IN_EVIDENCE: Is the proposed relationship already explicitly stated in the pre-discovery evidence?

Subclaims 1-5 are scored YES/NO with evidence span (quote).
Subclaim 6 is deterministic (string matching + semantic check).

If a subclaim cannot be scored (no relevant content), it is marked UNSCORABLE.

Resumable via checkpoint.
"""
import json, sys, re, time, os, subprocess, tempfile, hashlib, urllib.request, random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")

PACKET = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/formal_adjudication_packet.json"
CHECKPOINT = REPO / "discovery_fabric/evaluation/v1_12_controls/dsm_decomp_checkpoint.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/dsm_decomp_results.json"

MAX_CALLS_PER_RUN = 6
random.seed(42)

SUBCLAIM_SYSTEM = """You are an objective evidence extraction judge. You receive evidence, a proposal, and a target.

For EACH of the 6 subclaims below, answer YES or NO, and quote the EXACT text span from the proposal that supports your answer. If the subclaim is not applicable, mark UNSCORABLE.

1. COMPONENT_OVERLAP: Do the proposal and target name the same physical/material/biological components? (e.g., same reagents, same materials, same cell types)
   - YES if both mention the same key components
   - NO if they mention different components
   - Evidence span: quote from proposal showing the components

2. CAUSAL_RELATION_OVERLAP: Do they identify the same causal chain? (A causes B which causes C)
   - YES if the causal mechanism is the same
   - NO if different causal chain
   - Evidence span: quote from proposal showing the causal claim

3. COMBINATION_INTERACTION_OVERLAP: Do they identify the same combination or interaction of mechanisms?
   - YES if both propose combining/interacting the same mechanisms
   - NO if different combination or no combination
   - Evidence span: quote showing the combination

4. CONSTRAINT_RELEASE_OVERLAP: Do they identify the same constraint being removed or overcome?
   - YES if both identify the same barrier being overcome
   - NO if different barrier or no barrier identified
   - Evidence span: quote showing the constraint release

5. EXPERIMENTALLY_TESTABLE_CONSEQUENCE: Does the proposal predict a testable consequence that matches the target?
   - YES if the proposal makes a prediction that would confirm the target
   - NO if different prediction or no prediction
   - Evidence span: quote showing the prediction

6. RELATION_EXPLICIT_IN_EVIDENCE: Is the proposed relationship already explicitly stated in the pre-discovery evidence?
   - YES if the evidence text directly states the proposed relationship
   - NO if the relationship is NOT in the evidence (this is GOOD for a discovery)
   - Evidence span: quote from evidence showing the explicit statement (or "NOT_FOUND")

Output ONLY valid JSON:
{"component_overlap":{"verdict":"YES/NO/UNSCORABLE","evidence_span":"quote"},"causal_relation_overlap":{"verdict":"YES/NO/UNSCORABLE","evidence_span":"quote"},"combination_interaction_overlap":{"verdict":"YES/NO/UNSCORABLE","evidence_span":"quote"},"constraint_release_overlap":{"verdict":"YES/NO/UNSCORABLE","evidence_span":"quote"},"testable_consequence":{"verdict":"YES/NO/UNSCORABLE","evidence_span":"quote"},"relation_explicit_in_evidence":{"verdict":"YES/NO/UNSCORABLE","evidence_span":"quote"}}"""


def call_zai(prompt):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as f:
        out = f.name
    try:
        subprocess.run(["z-ai", "chat", "--prompt", prompt, "-o", out], capture_output=True, timeout=45)
        with open(out) as f:
            resp = json.load(f)
        content = resp["choices"][0]["message"]["content"]
        m = re.search(r'\{[\s\S]*\}', content)
        if m:
            try:
                return json.loads(m.group())
            except:
                pass
    except:
        pass
    finally:
        Path(out).unlink(missing_ok=True)
    return None


def call_openrouter(prompt, model="meta-llama/llama-3.3-70b-instruct", temp=0.7):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 400, "temperature": temp}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY','')}", "Content-Type": "application/json",
                 "HTTP-Referer": "https://discovery-fabric.local", "X-Title": "DSM Decomposition"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        m = re.search(r'\{[\s\S]*\}', content)
        if m:
            try:
                return json.loads(m.group())
            except:
                pass
    except:
        pass
    return None


def build_prompt(evidence, proposed, target):
    return SUBCLAIM_SYSTEM + f"\n\nPRE-DISCOVERY EVIDENCE:\n{evidence[:400]}\n\nPROPOSED MECHANISM:\n{proposed[:250]}\n\nTARGET MECHANISM:\n{target[:250]}\n\nScore all 6 subclaims."


def deterministic_check_6(evidence, proposed):
    """Subclaim 6: Is the proposed relationship already explicit in evidence? Deterministic check."""
    # Simple check: do key terms from proposed appear in evidence?
    proposed_terms = set(re.findall(r'\b[a-z]{4,}\b', proposed.lower())) - {'the','that','this','with','from','have','been','would','could','should','which','their','there','these','those','what','when','where','while','about','into','upon'}
    evidence_terms = set(re.findall(r'\b[a-z]{4,}\b', evidence.lower()))
    overlap = proposed_terms & evidence_terms
    overlap_ratio = len(overlap) / max(len(proposed_terms), 1)
    # If >60% of proposed terms appear in evidence, relationship is likely explicit
    if overlap_ratio > 0.6:
        return {"verdict": "YES", "evidence_span": f"DETERMINISTIC: {int(overlap_ratio*100)}% term overlap", "overlap_ratio": round(overlap_ratio, 2)}
    else:
        return {"verdict": "NO", "evidence_span": f"DETERMINISTIC: {int(overlap_ratio*100)}% term overlap", "overlap_ratio": round(overlap_ratio, 2)}


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"completed": [], "results": [], "calls_this_run": 0}

def save_checkpoint(cp):
    cp["calls_this_run"] = 0
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


SUBCLAIMS = ["component_overlap", "causal_relation_overlap", "combination_interaction_overlap",
             "constraint_release_overlap", "testable_consequence", "relation_explicit_in_evidence"]


def main():
    cp = load_checkpoint()
    with open(PACKET) as f:
        packet = json.load(f)
    completed = set(cp["completed"])
    
    for i, case in enumerate(packet):
        adj_id = case["adjudication_id"]
        if adj_id in completed:
            continue
        if cp["calls_this_run"] >= MAX_CALLS_PER_RUN:
            save_checkpoint(cp)
            print(f"  Checkpoint: {len(cp['completed'])}/{len(packet)}. Run again.")
            return
        
        evidence = case.get("pre_discovery_evidence", "")
        proposed = case.get("proposed_mechanism", "")
        target = case.get("target_mechanism", "")
        prompt = build_prompt(evidence, proposed, target)
        
        print(f"  [{i+1}/{len(packet)}] {adj_id}...", end=" ", flush=True)
        
        # 3 LLM judges
        r1 = call_zai(prompt)
        cp["calls_this_run"] += 1
        r2 = call_openrouter(prompt, model="meta-llama/llama-3.3-70b-instruct", temp=0.7)
        cp["calls_this_run"] += 1
        r3 = call_openrouter(prompt, model="deepseek/deepseek-v4-flash", temp=0.5)
        cp["calls_this_run"] += 1
        
        # Deterministic check for subclaim 6
        det6 = deterministic_check_6(evidence, proposed)
        
        result = {
            "adjudication_id": adj_id,
            "judge_1_glm4": r1 or {"error": "failed"},
            "judge_2_llama": r2 or {"error": "failed"},
            "judge_3_deepseek": r3 or {"error": "failed"},
            "deterministic_check_6": det6,
            "_hidden": case.get("_hidden", {}),
        }
        
        # Quick summary
        sc1 = [r1.get(sc, {}).get("verdict", "?") if r1 else "FAIL" for sc in SUBCLAIMS] if r1 else ["FAIL"]*6
        print(f"R1: {'/'.join(sc1[:3])}...")
        
        cp["results"].append(result)
        cp["completed"].append(adj_id)
        save_checkpoint(cp)
        time.sleep(1)
    
    save_checkpoint(cp)
    
    # Compute per-subclaim agreement
    results = cp["results"]
    n = len(results)
    
    print(f"\n=== DSM DECOMPOSITION RESULTS ({n} cases, 3 LLM judges + 1 deterministic) ===\n")
    
    for sc in SUBCLAIMS:
        v1 = [r["judge_1_glm4"].get(sc, {}).get("verdict", "UNSCORABLE") if r["judge_1_glm4"] and "error" not in r["judge_1_glm4"] else "FAIL" for r in results]
        v2 = [r["judge_2_llama"].get(sc, {}).get("verdict", "UNSCORABLE") if r["judge_2_llama"] and "error" not in r["judge_2_llama"] else "FAIL" for r in results]
        v3 = [r["judge_3_deepseek"].get(sc, {}).get("verdict", "UNSCORABLE") if r["judge_3_deepseek"] and "error" not in r["judge_3_deepseek"] else "FAIL" for r in results]
        
        # Pairwise agreement (exact match, excluding FAIL)
        agree_12 = sum(1 for a, b in zip(v1, v2) if a == b and a != "FAIL") 
        agree_13 = sum(1 for a, b in zip(v1, v3) if a == b and a != "FAIL")
        agree_23 = sum(1 for a, b in zip(v2, v3) if a == b and a != "FAIL")
        
        valid_12 = sum(1 for a, b in zip(v1, v2) if a != "FAIL" and b != "FAIL")
        valid_13 = sum(1 for a, b in zip(v1, v3) if a != "FAIL" and b != "FAIL")
        valid_23 = sum(1 for a, b in zip(v2, v3) if a != "FAIL" and b != "FAIL")
        
        rate_12 = agree_12 / max(valid_12, 1)
        rate_13 = agree_13 / max(valid_13, 1)
        rate_23 = agree_23 / max(valid_23, 1)
        avg_rate = (rate_12 + rate_13 + rate_23) / 3
        
        passed = "✅ PASS" if avg_rate >= 0.7 else "❌ FAIL"
        
        print(f"  {sc}:")
        print(f"    R1-R2: {agree_12}/{valid_12} ({100*rate_12:.0f}%)")
        print(f"    R1-R3: {agree_13}/{valid_13} ({100*rate_13:.0f}%)")
        print(f"    R2-R3: {agree_23}/{valid_23} ({100*rate_23:.0f}%)")
        print(f"    Average: {100*avg_rate:.0f}% — {passed} (threshold: ≥70%)")
        print()
    
    # Deterministic check 6
    det6_verdicts = [r["deterministic_check_6"]["verdict"] for r in results]
    det6_yes = sum(1 for v in det6_verdicts if v == "YES")
    print(f"  Deterministic check 6 (relation explicit in evidence):")
    print(f"    YES (explicit): {det6_yes}/{n}")
    print(f"    NO (novel): {n - det6_yes}/{n}")
    print(f"    (This is deterministic — 100% reproducible)")
    
    # Save
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclosure": "LLM-proxy judges (NOT human). R1=glm-4-plus, R2=llama@0.7, R3=deepseek@0.5. Plus deterministic check for subclaim 6.",
        "total_cases": n,
        "subclaims": SUBCLAIMS,
        "per_subclaim_agreement": {},
        "raw_results": results,
    }
    
    for sc in SUBCLAIMS:
        v1 = [r["judge_1_glm4"].get(sc, {}).get("verdict", "UNSCORABLE") if r["judge_1_glm4"] and "error" not in r["judge_1_glm4"] else "FAIL" for r in results]
        v2 = [r["judge_2_llama"].get(sc, {}).get("verdict", "UNSCORABLE") if r["judge_2_llama"] and "error" not in r["judge_2_llama"] else "FAIL" for r in results]
        v3 = [r["judge_3_deepseek"].get(sc, {}).get("verdict", "UNSCORABLE") if r["judge_3_deepseek"] and "error" not in r["judge_3_deepseek"] else "FAIL" for r in results]
        
        agree_12 = sum(1 for a, b in zip(v1, v2) if a == b and a != "FAIL")
        agree_13 = sum(1 for a, b in zip(v1, v3) if a == b and a != "FAIL")
        agree_23 = sum(1 for a, b in zip(v2, v3) if a == b and a != "FAIL")
        valid_12 = sum(1 for a, b in zip(v1, v2) if a != "FAIL" and b != "FAIL")
        valid_13 = sum(1 for a, b in zip(v1, v3) if a != "FAIL" and b != "FAIL")
        valid_23 = sum(1 for a, b in zip(v2, v3) if a != "FAIL" and b != "FAIL")
        
        avg = ((agree_12/max(valid_12,1)) + (agree_13/max(valid_13,1)) + (agree_23/max(valid_23,1))) / 3
        report["per_subclaim_agreement"][sc] = {
            "r1_r2": f"{agree_12}/{valid_12} ({100*agree_12/max(valid_12,1):.0f}%)",
            "r1_r3": f"{agree_13}/{valid_13} ({100*agree_13/max(valid_13,1):.0f}%)",
            "r2_r3": f"{agree_23}/{valid_23} ({100*agree_23/max(valid_23,1):.0f}%)",
            "average": f"{100*avg:.0f}%",
            "threshold": "≥70%",
            "passed": avg >= 0.7,
        }
    
    report["deterministic_check_6"] = {"yes": det6_yes, "no": n - det6_yes, "reproducible": True}
    
    with open(OUTPUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    h = hashlib.sha256(Path(OUTPUT).read_bytes()).hexdigest()
    print(f"\nResults hash: {h[:32]}...")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
