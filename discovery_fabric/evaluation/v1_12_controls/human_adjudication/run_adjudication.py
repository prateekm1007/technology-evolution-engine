"""
Human Adjudication Runner — obtains 2 independent LLM-proxy reviews per case.

DISCLOSURE: These are LLM-based proxies for human judgment, not actual human reviewers.
Reviewer A uses z-ai CLI (glm-4-plus) — different model from V3 scorer.
Reviewer B uses OpenRouter (meta-llama) with temperature=0.7 — different from V3's 0.3.

This is a known limitation. The results measure LLM-proxy inter-rater agreement,
not true human agreement. Human expert review remains the gold standard.

Resumable via checkpoint. Run repeatedly until complete.
"""
import json, sys, re, time, os, subprocess, tempfile, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")
from discovery_fabric.connectors.openrouter_llm import chat_text

PACKET = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/enriched_blinded_packet.json"
KEY = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/adjudication_key.json"
CHECKPOINT = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/adjudication_checkpoint.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/adjudication_results.json"

MAX_CALLS_PER_RUN = 6

REVIEWER_PROMPT = """You are an independent scientific reviewer evaluating a discovery proposal.

PRE-DISCOVERY EVIDENCE:
{evidence}

PROPOSED MECHANISM:
{proposed}

TARGET MECHANISM:
{target}

Questions:
A. Does the PROPOSAL identify the same RELATIONSHIP/COMBINATION/CONSTRAINT RELEASE as the TARGET? (YES/PARTIAL/NO)
B. Does the PROPOSAL mention the same mechanisms/components as the TARGET? (YES/PARTIAL/NO)
C. Is the TARGET a real historical discovery or fabricated? (REAL/FABRICATED/UNCERTAIN)
D. Your confidence: 0.0-1.0

Output ONLY JSON: {{"discovery_structure_match":"","mechanism_match":"","real_or_fabricated":"","confidence":0.0,"reasoning":""}}"""


def reviewer_a_zai(evidence, proposed, target):
    """Reviewer A: z-ai CLI (glm-4-plus) — different model from V3."""
    prompt = REVIEWER_PROMPT.format(evidence=evidence[:400], proposed=proposed[:200], target=target[:200])
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


def reviewer_b_llama(evidence, proposed, target):
    """Reviewer B: meta-llama via OpenRouter with temperature=0.7."""
    prompt = REVIEWER_PROMPT.format(evidence=evidence[:400], proposed=proposed[:200], target=target[:200])
    
    import urllib.request
    body = json.dumps({
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.7,  # Different from V3's 0.3
    }).encode()
    
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY','')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://discovery-fabric.local",
            "X-Title": "Discovery Fabric Adjudication",
        },
    )
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
    with open(KEY) as f:
        key = json.load(f)
    
    completed = set(cp["completed"])
    
    for i, (case, k) in enumerate(zip(packet, key)):
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
        
        # Reviewer A (z-ai)
        r_a = reviewer_a_zai(evidence, proposed, target)
        cp["calls_this_run"] += 1
        
        # Reviewer B (llama, temp=0.7)
        r_b = reviewer_b_llama(evidence, proposed, target)
        cp["calls_this_run"] += 1
        
        result = {
            "adjudication_id": adj_id,
            "reviewer_a": r_a or {"error": "failed"},
            "reviewer_b": r_b or {"error": "failed"},
            "_key": k,  # Original V3 scores and labels (for comparison, NOT shown to reviewers)
        }
        
        dsm_a = r_a.get("discovery_structure_match", "?") if r_a else "FAIL"
        dsm_b = r_b.get("discovery_structure_match", "?") if r_b else "FAIL"
        print(f"A={dsm_a} B={dsm_b}")
        
        cp["results"].append(result)
        cp["completed"].append(adj_id)
        save_checkpoint(cp)
        time.sleep(1)
    
    # ALL COMPLETE — compute agreement
    save_checkpoint(cp)
    
    print("\n=== ADJUDICATION COMPLETE ===\n")
    
    results = cp["results"]
    
    # Extract judgments
    a_dsm = [r["reviewer_a"].get("discovery_structure_match","NO") if r["reviewer_a"] else "FAIL" for r in results]
    b_dsm = [r["reviewer_b"].get("discovery_structure_match","NO") if r["reviewer_b"] else "FAIL" for r in results]
    v3_dsm = [r["_key"].get("_v3_dsm","NO") for r in results]
    
    a_mm = [r["reviewer_a"].get("mechanism_match","NO") if r["reviewer_a"] else "FAIL" for r in results]
    b_mm = [r["reviewer_b"].get("mechanism_match","NO") if r["reviewer_b"] else "FAIL" for r in results]
    v3_mm = [r["_key"].get("_v3_mm","NO") for r in results]
    
    a_real = [r["reviewer_a"].get("real_or_fabricated","UNCERTAIN") if r["reviewer_a"] else "FAIL" for r in results]
    b_real = [r["reviewer_b"].get("real_or_fabricated","UNCERTAIN") if r["reviewer_b"] else "FAIL" for r in results]
    actual_type = [r["_key"].get("_original_case_type","real") for r in results]
    
    # Inter-rater agreement (A vs B)
    dsm_agree = sum(1 for a, b in zip(a_dsm, b_dsm) if a == b)
    mm_agree = sum(1 for a, b in zip(a_mm, b_mm) if a == b)
    real_agree = sum(1 for a, b in zip(a_real, b_real) if a == b)
    
    # V3 vs human (using A as proxy)
    v3_vs_a_dsm = sum(1 for v, a in zip(v3_dsm, a_dsm) if v == a)
    v3_vs_a_mm = sum(1 for v, a in zip(v3_mm, a_mm) if v == a)
    
    # V3 false positives (V3 says YES on fabricated)
    v3_fp = sum(1 for v, t in zip(v3_dsm, actual_type) if v == "YES" and t == "false")
    # V3 false negatives (V3 says NO on real)
    v3_fn = sum(1 for v, t in zip(v3_dsm, actual_type) if v == "NO" and t == "real")
    
    # Human false positives (A says YES on fabricated)
    human_fp = sum(1 for a, t in zip(a_dsm, actual_type) if a == "YES" and t == "false")
    human_fn = sum(1 for a, t in zip(a_dsm, actual_type) if a == "NO" and t == "real")
    
    print(f"Inter-rater agreement (A vs B):")
    print(f"  DSM: {dsm_agree}/{len(results)} ({100*dsm_agree/len(results):.0f}%)")
    print(f"  MM:  {mm_agree}/{len(results)} ({100*mm_agree/len(results):.0f}%)")
    print(f"  Real/Fab: {real_agree}/{len(results)} ({100*real_agree/len(results):.0f}%)")
    print()
    print(f"V3 vs Reviewer A agreement:")
    print(f"  DSM: {v3_vs_a_dsm}/{len(results)} ({100*v3_vs_a_dsm/len(results):.0f}%)")
    print(f"  MM:  {v3_vs_a_mm}/{len(results)} ({100*v3_vs_a_mm/len(results):.0f}%)")
    print()
    print(f"V3 false positives: {v3_fp}")
    print(f"V3 false negatives: {v3_fn}")
    print(f"Human (A) false positives: {human_fp}")
    print(f"Human (A) false negatives: {human_fn}")
    
    # Save
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclosure": "LLM-proxy adjudication (not human experts). Reviewer A=glm-4-plus, B=llama-3.3-70b@0.7. V3=llama-3.3-70b@0.3.",
        "total_cases": len(results),
        "inter_rater_agreement": {
            "dsm": f"{dsm_agree}/{len(results)} ({100*dsm_agree/len(results):.0f}%)",
            "mm": f"{mm_agree}/{len(results)} ({100*mm_agree/len(results):.0f}%)",
            "real_fabricated": f"{real_agree}/{len(results)} ({100*real_agree/len(results):.0f}%)",
        },
        "v3_vs_human_agreement": {
            "dsm": f"{v3_vs_a_dsm}/{len(results)} ({100*v3_vs_a_dsm/len(results):.0f}%)",
            "mm": f"{v3_vs_a_mm}/{len(results)} ({100*v3_vs_a_mm/len(results):.0f}%)",
        },
        "v3_false_positives": v3_fp,
        "v3_false_negatives": v3_fn,
        "human_false_positives": human_fp,
        "human_false_negatives": human_fn,
        "raw_results": results,
    }
    
    with open(OUTPUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Hash
    h = hashlib.sha256(Path(OUTPUT).read_bytes()).hexdigest()
    print(f"\nResults hash: {h[:32]}...")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
