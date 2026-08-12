"""
Build the formal adjudication packet using Rubric V1.

Each case has:
- Pre-discovery evidence
- Proposed mechanism
- Target mechanism
- 5 questions (MR, DS, SS, HR, Confidence, Reasoning)

Reviewer sees NOTHING else.
3 reviewers needed per case.
"""
import json, hashlib, random
from pathlib import Path

random.seed(42)

REPO = Path(__file__).resolve().parents[4]

# Load enriched packet
with open(REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/enriched_blinded_packet.json") as f:
    packet = json.load(f)

with open(REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication/adjudication_key.json") as f:
    key = json.load(f)

# Build formal adjudication packet
formal = []
for p, k in zip(packet, key):
    formal.append({
        "adjudication_id": p["adjudication_id"],
        "pre_discovery_evidence": p["pre_discovery_evidence"],
        "proposed_mechanism": p["proposed_mechanism"],
        "target_mechanism": p["target_mechanism"],
        "rubric": {
            "MR": "Does the proposal identify the same physical/chemical/biological mechanisms or components as the target? (YES/NO)",
            "DS": "Does the proposal identify the same RELATIONSHIP/COMBINATION/CONSTRAINT RELEASE that makes the target a discovery? (2=FULL, 1=PARTIAL, 0=NONE)",
            "SS": "Would the proposal have been sufficient to motivate the historical experiment? (YES/NO)",
            "HR": "Is the target a real historical discovery or fabricated? (REAL/FABRICATED)",
            "confidence": "Your confidence: 0.0-1.0",
            "reasoning": "Brief reasoning (1-2 sentences)",
        },
        "output_format": 'Output JSON: {"MR":"","DS":0,"SS":"","HR":"","confidence":0.0,"reasoning":""}',
        "blinded": True,
        "_hidden": {
            "config": k.get("_original_config", ""),
            "case_type": k.get("_original_case_type", ""),
            "v3_dsm": k.get("_v3_dsm", ""),
            "v3_mm": k.get("_v3_mm", ""),
        },
    })

output_dir = REPO / "discovery_fabric/evaluation/v1_12_controls/human_adjudication"

with open(output_dir / "formal_adjudication_packet.json", "w") as f:
    json.dump(formal, f, indent=2)

h = hashlib.sha256(Path(output_dir / "formal_adjudication_packet.json").read_bytes()).hexdigest()
print(f"Formal adjudication packet: {len(formal)} cases")
print(f"Hash: {h[:32]}...")
print(f"Rubric: MR (binary), DS (0-2 ordinal), SS (binary), HR (binary), Confidence (0-1)")
print(f"Reviewer sees: evidence, proposed, target, rubric questions")
print(f"Reviewer does NOT see: config, V3 score, real/fabricated label, discovery name")
print(f"\nAcceptance criteria:")
print(f"  DS pairwise agreement ≥ 70% (within 1 point)")
print(f"  MR pairwise agreement ≥ 80%")
print(f"  HR pairwise agreement ≥ 70%")
print(f"  Majority consensus for ≥ 90% of cases")
