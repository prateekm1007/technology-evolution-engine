"""
Formal Adjudication Runner — 3 LLM-proxy reviewers using Rubric V1.

DISCLOSURE: These are LLM-based proxies, NOT human experts.
Reviewer 1: z-ai CLI (glm-4-plus)
Reviewer 2: OpenRouter (meta-llama/llama-3.3-70b-instruct) at temp=0.7
Reviewer 3: OpenRouter (deepseek/deepseek-v4-flash) — different model family

All reviewers use the SAME formal rubric (MR, DS, SS, HR, Confidence).
Reviewers are blind to: config, V3 score, real/fabricated label, discovery name.

Resumable via checkpoint.
"""
import json, sys, re, time, os, subprocess, tempfile, hashlib, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")

PACKET = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/formal_adjudication_packet.json"
CHECKPOINT = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/formal_checkpoint.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/formal_adjudication_results.json"

MAX_CALLS_PER_RUN = 6

RUBRIC_PROMPT = """You are an independent scientific reviewer. Use this rubric:

PRE-DISCOVERY EVIDENCE:
{evidence}

PROPOSED MECHANISM:
{proposed}

TARGET MECHANISM:
{target}

Answer each question:
1. MR: Does the proposal identify the same mechanisms/components as the target? (YES/NO)
2. DS: Does the proposal identify the same RELATIONSHIP/COMBINATION/CONSTRAINT RELEASE? (2=FULL, 1=PARTIAL, 0=NONE)
3. SS: Would the proposal motivate the historical experiment? (YES/NO)
4. HR: Is the target real or fabricated? (REAL/FABRICATED)
5. Confidence: 0.0-1.0

Output ONLY JSON: {{"MR":"","DS":0,"SS":"","HR":"","confidence":0.0,"reasoning":""}}"""


def reviewer_zai(evidence, proposed, target):
    prompt = RUBRIC_PROMPT.format(evidence=evidence[:400], proposed=proposed[:200], target=target[:200])
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as f:
        out = f.name
    try:
        subprocess.run(["z-ai", "chat", "--prompt", prompt, "-o", out], capture_output=True, timeout=45)
        with open(out) as f:
            resp = json.load(f)
        content = resp["choices"][0]["message"]["content"]
        m = re.search(r'\{[^}]+\}', content)
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


def reviewer_openrouter(evidence, proposed, target, model="meta-llama/llama-3.3-70b-instruct", temp=0.7):
    prompt = RUBRIC_PROMPT.format(evidence=evidence[:400], proposed=proposed[:200], target=target[:200])
    body = json.dumps({
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200, "temperature": temp,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY','')}",
                 "Content-Type": "application/json", "HTTP-Referer": "https://discovery-fabric.local",
                 "X-Title": "Discovery Fabric Adjudication"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        m = re.search(r'\{[^}]+\}', content)
        if m:
            try:
                return json.loads(m.group())
            except:
                pass
    except:
        pass
    return None


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"completed": [], "results": [], "calls_this_run": 0}

def save_checkpoint(cp):
    cp["calls_this_run"] = 0
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


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
        
        print(f"  [{i+1}/{len(packet)}] {adj_id}...", end=" ", flush=True)
        
        # 3 reviewers
        r1 = reviewer_zai(evidence, proposed, target)
        cp["calls_this_run"] += 1
        r2 = reviewer_openrouter(evidence, proposed, target, model="meta-llama/llama-3.3-70b-instruct", temp=0.7)
        cp["calls_this_run"] += 1
        r3 = reviewer_openrouter(evidence, proposed, target, model="deepseek/deepseek-v4-flash", temp=0.5)
        cp["calls_this_run"] += 1
        
        result = {
            "adjudication_id": adj_id,
            "reviewer_1_glm4": r1 or {"error": "failed"},
            "reviewer_2_llama": r2 or {"error": "failed"},
            "reviewer_3_deepseek": r3 or {"error": "failed"},
            "_hidden": case.get("_hidden", {}),
        }
        
        ds1 = r1.get("DS", "?") if r1 else "FAIL"
        ds2 = r2.get("DS", "?") if r2 else "FAIL"
        ds3 = r3.get("DS", "?") if r3 else "FAIL"
        print(f"DS: {ds1}/{ds2}/{ds3}")
        
        cp["results"].append(result)
        cp["completed"].append(adj_id)
        save_checkpoint(cp)
        time.sleep(1)
    
    save_checkpoint(cp)
    
    # Compute agreement
    results = cp["results"]
    
    # Extract DS (0/1/2) for each reviewer
    ds1 = [r["reviewer_1_glm4"].get("DS", -1) if r["reviewer_1_glm4"] else -1 for r in results]
    ds2 = [r["reviewer_2_llama"].get("DS", -1) if r["reviewer_2_llama"] else -1 for r in results]
    ds3 = [r["reviewer_3_deepseek"].get("DS", -1) if r["reviewer_3_deepseek"] else -1 for r in results]
    
    mr1 = [r["reviewer_1_glm4"].get("MR", "?") if r["reviewer_1_glm4"] else "FAIL" for r in results]
    mr2 = [r["reviewer_2_llama"].get("MR", "?") if r["reviewer_2_llama"] else "FAIL" for r in results]
    mr3 = [r["reviewer_3_deepseek"].get("MR", "?") if r["reviewer_3_deepseek"] else "FAIL" for r in results]
    
    hr1 = [r["reviewer_1_glm4"].get("HR", "?") if r["reviewer_1_glm4"] else "FAIL" for r in results]
    hr2 = [r["reviewer_2_llama"].get("HR", "?") if r["reviewer_2_llama"] else "FAIL" for r in results]
    hr3 = [r["reviewer_3_deepseek"].get("HR", "?") if r["reviewer_3_deepseek"] else "FAIL" for r in results]
    
    # Pairwise agreement (DS within 1 point)
    ds_12 = sum(1 for a, b in zip(ds1, ds2) if abs(a - b) <= 1 and a >= 0 and b >= 0)
    ds_13 = sum(1 for a, b in zip(ds1, ds3) if abs(a - b) <= 1 and a >= 0 and b >= 0)
    ds_23 = sum(1 for a, b in zip(ds2, ds3) if abs(a - b) <= 1 and a >= 0 and b >= 0)
    
    mr_12 = sum(1 for a, b in zip(mr1, mr2) if a == b and a != "FAIL")
    mr_13 = sum(1 for a, b in zip(mr1, mr3) if a == b and a != "FAIL")
    mr_23 = sum(1 for a, b in zip(mr2, mr3) if a == b and a != "FAIL")
    
    hr_12 = sum(1 for a, b in zip(hr1, hr2) if a == b and a != "FAIL")
    hr_13 = sum(1 for a, b in zip(hr1, hr3) if a == b and a != "FAIL")
    hr_23 = sum(1 for a, b in zip(hr2, hr3) if a == b and a != "FAIL")
    
    n = len(results)
    
    print(f"\n=== FORMAL ADJUDICATION RESULTS ({n} cases, 3 reviewers) ===\n")
    print(f"DS pairwise agreement (within 1 point):")
    print(f"  R1 vs R2: {ds_12}/{n} ({100*ds_12/n:.0f}%)")
    print(f"  R1 vs R3: {ds_13}/{n} ({100*ds_13/n:.0f}%)")
    print(f"  R2 vs R3: {ds_23}/{n} ({100*ds_23/n:.0f}%)")
    print(f"  Average: {100*(ds_12+ds_13+ds_23)/(3*n):.0f}%")
    print(f"  Threshold: ≥70%")
    print()
    print(f"MR pairwise agreement:")
    print(f"  R1 vs R2: {mr_12}/{n} ({100*mr_12/n:.0f}%)")
    print(f"  R1 vs R3: {mr_13}/{n} ({100*mr_13/n:.0f}%)")
    print(f"  R2 vs R3: {mr_23}/{n} ({100*mr_23/n:.0f}%)")
    print(f"  Average: {100*(mr_12+mr_13+mr_23)/(3*n):.0f}%")
    print(f"  Threshold: ≥80%")
    print()
    print(f"HR pairwise agreement:")
    print(f"  R1 vs R2: {hr_12}/{n} ({100*hr_12/n:.0f}%)")
    print(f"  R1 vs R3: {hr_13}/{n} ({100*hr_13/n:.0f}%)")
    print(f"  R2 vs R3: {hr_23}/{n} ({100*hr_23/n:.0f}%)")
    print(f"  Average: {100*(hr_12+hr_13+hr_23)/(3*n):.0f}%")
    print(f"  Threshold: ≥70%")
    
    # V3 comparison
    v3_dsm = [r["_hidden"].get("v3_dsm", "?") for r in results]
    v3_mm = [r["_hidden"].get("v3_mm", "?") for r in results]
    
    # Map V3 to DS scale: YES=2, PARTIAL=1, NO=0
    v3_ds = [{"YES": 2, "PARTIAL": 1, "NO": 0}.get(v, -1) for v in v3_dsm]
    
    # Consensus DS (median of 3)
    consensus_ds = []
    for a, b, c in zip(ds1, ds2, ds3):
        vals = sorted([v for v in [a, b, c] if v >= 0])
        if vals:
            consensus_ds.append(vals[len(vals)//2])  # median
        else:
            consensus_ds.append(-1)
    
    v3_vs_consensus = sum(1 for v, c in zip(v3_ds, consensus_ds) if v == c and v >= 0)
    
    print(f"\nV3 vs consensus DS: {v3_vs_consensus}/{n} ({100*v3_vs_consensus/n:.0f}%)")
    
    # Save
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclosure": "LLM-proxy adjudication (NOT human experts). R1=glm-4-plus, R2=llama-3.3-70b@0.7, R3=deepseek-v4-flash@0.5. V3=llama-3.3-70b@0.3.",
        "rubric_version": "V1_FROZEN",
        "total_cases": n,
        "ds_pairwise_agreement": {"r1_r2": f"{100*ds_12/n:.0f}%", "r1_r3": f"{100*ds_13/n:.0f}%", "r2_r3": f"{100*ds_23/n:.0f}%", "average": f"{100*(ds_12+ds_13+ds_23)/(3*n):.0f}%", "threshold": "≥70%"},
        "mr_pairwise_agreement": {"r1_r2": f"{100*mr_12/n:.0f}%", "r1_r3": f"{100*mr_13/n:.0f}%", "r2_r3": f"{100*mr_23/n:.0f}%", "average": f"{100*(mr_12+mr_13+mr_23)/(3*n):.0f}%", "threshold": "≥80%"},
        "hr_pairwise_agreement": {"r1_r2": f"{100*hr_12/n:.0f}%", "r1_r3": f"{100*hr_13/n:.0f}%", "r2_r3": f"{100*hr_23/n:.0f}%", "average": f"{100*(hr_12+hr_13+hr_23)/(3*n):.0f}%", "threshold": "≥70%"},
        "v3_vs_consensus_ds": f"{v3_vs_consensus}/{n} ({100*v3_vs_consensus/n:.0f}%)",
        "raw_results": results,
    }
    
    with open(OUTPUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    h = hashlib.sha256(Path(OUTPUT).read_bytes()).hexdigest()
    print(f"\nResults hash: {h[:32]}...")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
