"""
Structured Mechanism Extractor.

Extracts 10-field structured mechanisms from evidence abstracts using LLM.

Fields:
  OBJECTIVE, INPUT, PROCESS, INTERMEDIATE_STATE, OUTPUT,
  MEASURED_EFFECT, OPERATING_CONDITIONS, CONSTRAINTS, FAILURE_MODE, CONTROL

Critical rule: LLM must NEVER invent missing fields. Missing = UNKNOWN.
Every extracted element points back to source evidence.
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
MECHANISMS_DIR = REPO / "discovery_fabric/mechanisms"
MECHANISMS_DIR.mkdir(parents=True, exist_ok=True)

UNKNOWN = "UNKNOWN"

MECHANISM_FIELDS = [
    "OBJECTIVE", "INPUT", "PROCESS", "INTERMEDIATE_STATE", "OUTPUT",
    "MEASURED_EFFECT", "OPERATING_CONDITIONS", "CONSTRAINTS", "FAILURE_MODE", "CONTROL",
]

SYSTEM_PROMPT = """You are a mechanism extractor for a scientific discovery engine. Extract a structured mechanism from the given scientific paper abstract.

Extract these 10 fields:
- OBJECTIVE: What problem or goal does this work address?
- INPUT: What is the starting material, system, or condition?
- PROCESS: What transformation or method is applied?
- INTERMEDIATE_STATE: What intermediate state or change occurs?
- OUTPUT: What is the resulting material, system, or state?
- MEASURED_EFFECT: What quantitative or qualitative effect is measured?
- OPERATING_CONDITIONS: Under what conditions does this operate?
- CONSTRAINTS: What limits or constrains this mechanism?
- FAILURE_MODE: Under what conditions does this fail or degrade?
- CONTROL: What control or comparison is used?

CRITICAL RULES:
1. Extract ONLY what is directly stated or clearly implied in the abstract.
2. If a field is not mentioned, output "UNKNOWN" — NEVER guess or invent.
3. Be specific — quote key terms from the abstract where possible.
4. Every extracted field must trace back to text in the abstract.

Output ONLY valid JSON:
{
  "OBJECTIVE": "...",
  "INPUT": "...",
  "PROCESS": "...",
  "INTERMEDIATE_STATE": "...",
  "OUTPUT": "...",
  "MEASURED_EFFECT": "...",
  "OPERATING_CONDITIONS": "...",
  "CONSTRAINTS": "...",
  "FAILURE_MODE": "...",
  "CONTROL": "..."
}"""


def extract_mechanism_llm(title, abstract, evidence_id):
    """Use LLM to extract structured mechanism from abstract."""
    try:
        import ZAI
        zai = ZAI.create()
    except Exception:
        return None, "z-ai-web-dev-sdk not available"

    user_prompt = f"""Paper ID: {evidence_id}
Title: {title}

Abstract: {abstract[:1500]}

Extract the 10-field structured mechanism as JSON. Use "UNKNOWN" for any field not mentioned."""

    try:
        completion = zai.chat.completions.create(
            messages=[
                {"role": "assistant", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            thinking={"type": "disabled"},
        )
        content = completion.choices[0].message.content or "{}"
        # Strip markdown
        content = content.strip().strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()
        mechanism = json.loads(content)

        # Validate all fields present, fill missing with UNKNOWN
        for field in MECHANISM_FIELDS:
            if field not in mechanism or not mechanism[field]:
                mechanism[field] = UNKNOWN

        return mechanism, "success"
    except json.JSONDecodeError:
        return None, "json_parse_error"
    except Exception as e:
        return None, f"error: {type(e).__name__}: {str(e)[:100]}"


def extract_mechanism_keyword(title, abstract):
    """Fallback keyword-based extraction when LLM unavailable."""
    text = (title + " " + abstract).lower()
    mechanism = {}

    # OBJECTIVE
    mechanism["OBJECTIVE"] = title[:200] if title else UNKNOWN

    # INPUT — look for materials/substances
    materials = [m for m in ["lithium", "silicon", "graphene", "polymer", "carbon", "protein", "dna", "metal", "ceramic", "perovskite"] if m in text]
    mechanism["INPUT"] = ", ".join(materials[:3]) if materials else UNKNOWN

    # PROCESS — look for process verbs
    processes = [p for p in ["synthesis", "deposition", "treatment", "fabrication", "annealing", "coating", "doping", "etching", "deposition", "modification"] if p in text]
    mechanism["PROCESS"] = ", ".join(processes[:3]) if processes else UNKNOWN

    # MEASURED_EFFECT — look for numbers/percentages
    import re
    numbers = re.findall(r'\d+\.?\d*\s*%', text)
    mechanism["MEASURED_EFFECT"] = ", ".join(numbers[:3]) if numbers else UNKNOWN

    # Fill remaining as UNKNOWN
    for field in ["INTERMEDIATE_STATE", "OUTPUT", "OPERATING_CONDITIONS", "CONSTRAINTS", "FAILURE_MODE", "CONTROL"]:
        mechanism[field] = UNKNOWN

    mechanism["_extraction_method"] = "keyword_fallback"
    return mechanism


def main(max_items=200):
    """Extract structured mechanisms from evidence with abstracts."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Structured mechanism extraction starting")
    print(f"  max items: {max_items}")

    # Load evidence with abstracts
    evidence_with_abstracts = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                abstract = e.get("abstract", "")
                if abstract and abstract != "UNAVAILABLE" and len(abstract) > 50:
                    evidence_with_abstracts.append(e)

    print(f"  evidence with usable abstracts: {len(evidence_with_abstracts)}")

    # Process subset
    to_process = evidence_with_abstracts[:max_items]
    print(f"  processing: {len(to_process)}")

    mechanisms = []
    llm_success = 0
    llm_fail = 0
    keyword_fallback = 0

    for i, e in enumerate(to_process):
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(to_process)}] llm_ok={llm_success} llm_fail={llm_fail} kw={keyword_fallback}")

        title = e.get("title", "")
        abstract = e.get("abstract", "")
        eid = e["id"]

        mechanism, status = extract_mechanism_llm(title, abstract, eid)

        if mechanism and status == "success":
            llm_success += 1
            mechanism["_extraction_method"] = "llm"
        else:
            # Fallback to keyword
            mechanism = extract_mechanism_keyword(title, abstract)
            keyword_fallback += 1

        # Add provenance
        mechanism["evidence_id"] = eid
        mechanism["source"] = e.get("source", "")
        mechanism["domain"] = e.get("domain", "")
        mechanism["source_uri"] = e.get("source_uri", "")
        mechanism["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
        mechanism["mechanism_hash"] = hashlib.sha256(
            json.dumps(mechanism, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()

        mechanisms.append(mechanism)

    # Save
    output = MECHANISMS_DIR / "structured_mechanisms.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_mechanisms": len(mechanisms),
            "llm_extracted": llm_success,
            "keyword_fallback": keyword_fallback,
            "mechanisms": mechanisms,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] EXTRACTION COMPLETE")
    print(f"  total: {len(mechanisms)}")
    print(f"  llm: {llm_success}")
    print(f"  keyword fallback: {keyword_fallback}")
    print(f"  saved: {output}")

    # Stats on UNKNOWN rates
    unknown_rates = {}
    for field in MECHANISM_FIELDS:
        unknown_count = sum(1 for m in mechanisms if m.get(field) == UNKNOWN)
        unknown_rates[field] = f"{unknown_count}/{len(mechanisms)} ({100*unknown_count/len(mechanisms):.0f}%)"
    print(f"\n  UNKNOWN rates by field:")
    for field, rate in unknown_rates.items():
        print(f"    {field}: {rate}")

    return mechanisms


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=200)
    args = parser.parse_args()
    main(args.max_items)
