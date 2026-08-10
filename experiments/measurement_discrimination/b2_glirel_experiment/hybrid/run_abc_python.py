#!/usr/bin/env python3
"""run_abc_python.py — A/B/C experiment using direct HTTP calls to z-ai API.

Avoids Node.js process management issues. Uses Python requests with
checkpointing and resume capability.
"""
import json, os, sys, time, hashlib, requests
from pathlib import Path

HERE = Path(__file__).parent
EVIDENCE_PATH = HERE / "results" / "glirel" / "evidence_graphs_v3.json"
FIXTURE_PATH = HERE.parent.parent / "b2_adversarial_v2" / "test_fixture.json"
CHECKPOINT_PATH = HERE / "results" / "abc" / "checkpoint.json"
OUTPUT_PATH = HERE / "results" / "abc" / "abc_full_results.json"
CHECKPOINT_PATH.parent.mkdir(exist_ok=True)

# Read API config
import json as _json
with open("/etc/.z-ai-config") as f:
    cfg = _json.load(f)
API_URL = cfg["baseUrl"] + "/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {cfg['apiKey']}",
    "X-Z-AI-From": "Z",
}
if cfg.get("token"):
    HEADERS["X-Token"] = cfg["token"]
if cfg.get("chatId"):
    HEADERS["X-Chat-Id"] = cfg["chatId"]
if cfg.get("userId"):
    HEADERS["X-User-Id"] = cfg["userId"]

MODEL = "glm-4-plus"
REPS = ["A", "B", "C"]

BASE_PROMPT = """You are a B-2 leakage detection instrument with structured evidence assistance.

You receive: (1) a candidate phrase, (2) Source A and Source B texts, (3) structured evidence from GLiREL.

CRITICAL: GLiREL output is EVIDENCE EXTRACTION, NOT TRUTH. Verify independently.

Determine: ISS_one->REJECT, ISS_both->ALLOW, REDUNDANT_SUPPORT->ALLOW, UNSUPPORTED->NOT_ADJUDICATED_BY_B2.

Output ONLY JSON: {"classification":{"justified_by_corpus":bool,"iss_a":bool,"iss_b":bool,"iss_state":"...","label":"..."},"evidence_assessment":{"glirel_relations_available":int,"relations_relevant":int,"relations_cited":int,"glirel_evidence_helpful":bool,"false_evidence_cited":bool,"cited_relation_details":[],"rejected_relation_details":[],"notes":"..."}}"""

def build_prompt(rep, ev):
    sa, sb = ev["source_a"]["text"], ev["source_b"]["text"]
    ra, rb = ev["source_a"]["relations"], ev["source_b"]["relations"]
    cid, cand = ev["case_id"], ev["candidate"]

    if rep == "A":
        def fmt(r, i): return f"{i+1}. {r['label']}: {r['head_text']} -> {r['tail_text']} (score={r.get('score',0):.3f})"
        return f"CASE ID: {cid}\nCANDIDATE: {cand}\n\nSOURCE A:\n{sa}\n\nSOURCE B:\n{sb}\n\nGLiREL A:\n" + "\n".join(fmt(r,i) for i,r in enumerate(ra[:10])) + f"\n\nGLiREL B:\n" + "\n".join(fmt(r,i) for i,r in enumerate(rb[:10])) + "\n\nVerify independently. Output JSON."
    if rep == "B":
        def fmt(r, i): return f"{i+1}|{r['head_text']}|[{r['head_span']['start']},{r['head_span']['end']}]|{r['label']}|{r['tail_text']}|[{r['tail_span']['start']},{r['tail_span']['end']}]|{r.get('score',0):.3f}"
        return f"CASE ID: {cid}\nCANDIDATE: {cand}\n\nSOURCE A:\n{sa}\n\nSOURCE B:\n{sb}\n\nTABLE A:\n" + "\n".join(fmt(r,i) for i,r in enumerate(ra[:10])) + f"\n\nTABLE B:\n" + "\n".join(fmt(r,i) for i,r in enumerate(rb[:10])) + "\n\nAll spans valid. Verify source[start:end]==text. Output JSON."
    # C: graph
    na = "\n".join(f'  A{i}: "{e["text"]}" [{e["start"]},{e["end"]}] {e["label"]}' for i,e in enumerate(ev["source_a"]["entities"]))
    nb = "\n".join(f'  B{i}: "{e["text"]}" [{e["start"]},{e["end"]}] {e["label"]}' for i,e in enumerate(ev["source_b"]["entities"]))
    ea = "\n".join(f'  A_E{i}: "{r["head_text"]}" --[{r["label"]}]--> "{r["tail_text"]}" (score={r.get("score",0):.3f})' for i,r in enumerate(ra[:10]))
    eb = "\n".join(f'  B_E{i}: "{r["head_text"]}" --[{r["label"]}]--> "{r["tail_text"]}" (score={r.get("score",0):.3f})' for i,r in enumerate(rb[:10]))
    return f"CASE ID: {cid}\nCANDIDATE: {cand}\n\nSOURCE A:\n{sa}\n\nSOURCE B:\n{sb}\n\nGRAPH A:\nNodes:\n{na}\nEdges:\n{ea}\n\nGRAPH B:\nNodes:\n{nb}\nEdges:\n{eb}\n\nCANDIDATE OVERLAY: \"{cand}\"\nAll spans valid. Verify independently. Output JSON."

def call_api(prompt, max_retries=5):
    delay = 8
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(API_URL, headers=HEADERS, json={
                "model": MODEL,
                "messages": [{"role": "assistant", "content": BASE_PROMPT}, {"role": "user", "content": prompt}],
                "thinking": {"type": "disabled"},
            }, timeout=60)
            if resp.status_code == 429:
                print(f"    [retry {attempt}/{max_retries}] 429, waiting {delay}s...", flush=True)
                time.sleep(delay)
                delay *= 2
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            content = content.replace("```json\n", "").replace("```", "").strip()
            return content
        except Exception as e:
            if attempt < max_retries:
                print(f"    [retry {attempt}/{max_retries}] {e}, waiting {delay}s...", flush=True)
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise RuntimeError("Max retries exceeded")

def main():
    print("B-2 GLiREL A/B/C Full 13-Case (Python)", flush=True)
    print(f"Model: {MODEL}", flush=True)

    evidence = json.loads(EVIDENCE_PATH.read_text())
    fixture = json.loads(FIXTURE_PATH.read_text())

    # Load checkpoint
    if CHECKPOINT_PATH.exists():
        checkpoint = json.loads(CHECKPOINT_PATH.read_text())
    else:
        checkpoint = {"completed": {}, "results": []}

    for ev in evidence:
        tc = next((c for c in fixture["cases"] if c["id"] == ev["case_id"]), None)
        if not tc:
            continue
        amended = "NOT_ADJUDICATED_BY_B2" if ev["case_id"] == "ADV-09" else tc["expected_label"]
        cid = ev["case_id"]
        print(f"\n[{cid}] {ev['candidate']} (expected: {amended})", flush=True)

        # Find or create case result
        case_result = next((r for r in checkpoint["results"] if r["case_id"] == cid), None)
        if not case_result:
            case_result = {"case_id": cid, "candidate": ev["candidate"], "expected": amended}
            checkpoint["results"].append(case_result)

        for rep in REPS:
            check_key = f"{cid}_{rep}"
            if check_key in checkpoint["completed"]:
                v = case_result.get(rep, {})
                print(f"  {rep}: CACHED {v.get('label','?')} {v.get('match','?')}", flush=True)
                continue

            print(f"  {rep}: calling API...", end="", flush=True)
            try:
                prompt = build_prompt(rep, ev)
                content = call_api(prompt)
                try:
                    trace = json.loads(content)
                except:
                    trace = {"classification": {"label": "PARSE_ERROR"}, "evidence_assessment": {}}

                cls = trace.get("classification", {})
                ev_a = trace.get("evidence_assessment", {})
                label = cls.get("label", "ERROR")
                state = cls.get("iss_state", "UNKNOWN")
                match = label == amended

                case_result[rep] = {
                    "label": label, "state": state, "match": match,
                    "cited": ev_a.get("relations_cited", 0),
                    "available": ev_a.get("glirel_relations_available", 0),
                    "relevant": ev_a.get("relations_relevant", 0),
                    "helpful": ev_a.get("glirel_evidence_helpful"),
                    "false_citation": ev_a.get("false_evidence_cited", False),
                    "cited_details": ev_a.get("cited_relation_details", []),
                    "rejected_details": ev_a.get("rejected_relation_details", []),
                }

                checkpoint["completed"][check_key] = {
                    "status": "complete",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "sha256": hashlib.sha256(content.encode()).hexdigest()[:16],
                }

                print(f" {label} ({state}) {'OK' if match else 'X'} cited={case_result[rep]['cited']} false={case_result[rep]['false_citation']}", flush=True)
            except Exception as e:
                case_result[rep] = {"label": "ERROR", "state": "ERROR", "match": False, "cited": 0, "false_citation": False, "error": str(e)}
                checkpoint["completed"][check_key] = {"status": "error", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "error": str(e)}
                print(f" ERROR: {e}", flush=True)

            CHECKPOINT_PATH.write_text(json.dumps(checkpoint, indent=2))
            time.sleep(3)

    # Summary
    print("\n" + "=" * 70, flush=True)
    print("FULL A/B/C SUMMARY (13 cases)", flush=True)
    print("=" * 70, flush=True)
    for rep in REPS:
        results = [r.get(rep, {}) for r in checkpoint["results"]]
        results = [r for r in results if r]
        matches = sum(1 for r in results if r.get("match"))
        false_cit = sum(1 for r in results if r.get("false_citation"))
        total_cited = sum(r.get("cited", 0) for r in results)
        labels = {}
        for r in results:
            labels[r.get("label", "?")] = labels.get(r.get("label", "?"), 0) + 1
        print(f"\n{rep} ({'raw list' if rep=='A' else 'table' if rep=='B' else 'graph'}):", flush=True)
        print(f"  Accuracy: {matches}/{len(results)}", flush=True)
        print(f"  False citations: {false_cit}/{len(results)}", flush=True)
        print(f"  Total cited: {total_cited} (avg {total_cited/len(results):.1f})", flush=True)
        print(f"  Labels: {labels}", flush=True)

    # Per-case
    print("\nPER-CASE:", flush=True)
    print("-" * 70, flush=True)
    for r in checkpoint["results"]:
        parts = []
        for rep in REPS:
            v = r.get(rep, {})
            if v:
                parts.append(f"{rep}={v.get('label','?')}{'OK' if v.get('match') else 'X'}")
            else:
                parts.append(f"{rep}=N/A")
        print(f"  {r['case_id']}: {' | '.join(parts)}", flush=True)

    # Save final
    OUTPUT_PATH.write_text(json.dumps({
        "model": MODEL,
        "total_cases": len(checkpoint["results"]),
        "per_case": checkpoint["results"],
        "checkpoint": checkpoint["completed"],
    }, indent=2))
    print(f"\nResults: {OUTPUT_PATH}", flush=True)

if __name__ == "__main__":
    main()
