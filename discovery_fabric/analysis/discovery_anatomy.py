"""
Discovery Anatomy Analysis — classifies historical discoveries by pattern.
Answers: What fraction of known discovery patterns does the current engine cover?
"""
import json
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[2]

def analyze_discoveries():
    with open(REPO / "discovery_fabric/benchmarks/historical_discoveries/dataset.json") as f:
        discoveries = json.load(f)

    patterns = Counter(d["discovery_pattern"] for d in discoveries)

    ENGINE_COVERS = {
        "mechanism_transfer": True,
        "constraint_inversion": True,
        "combination_of_independently_validated_mechanisms": False,
        "contradiction_resolution": False,
        "unexpected_material_property": False,
        "rare_observation": False,
        "unexpected_observation": False,
        "new_synthesis_pathway": False,
        "new_capability_required": False,
    }

    analysis = {
        "total_discoveries": len(discoveries),
        "pattern_distribution": dict(patterns),
        "engine_coverage": {},
        "covered_count": 0,
        "uncovered_count": 0,
        "uncovered_discoveries": [],
    }

    for d in discoveries:
        pattern = d["discovery_pattern"]
        covered = ENGINE_COVERS.get(pattern, False)
        if covered:
            analysis["covered_count"] += 1
        else:
            analysis["uncovered_count"] += 1
            analysis["uncovered_discoveries"].append({
                "id": d["id"],
                "discovery": d["discovery"],
                "pattern": pattern,
                "why_missed": f"Engine does not implement {pattern} discovery mode"
            })

    for pattern, count in patterns.items():
        analysis["engine_coverage"][pattern] = {
            "count": count,
            "percentage": f"{100*count/len(discoveries):.0f}%",
            "engine_covers": ENGINE_COVERS.get(pattern, False),
        }

    coverage_rate = analysis["covered_count"] / analysis["total_discoveries"]
    analysis["coverage_rate"] = f"{100*coverage_rate:.0f}%"

    output = REPO / "discovery_fabric/analysis/discovery_anatomy.json"
    with open(output, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"=== DISCOVERY ANATOMY ANALYSIS ===")
    print(f"Total historical discoveries: {analysis['total_discoveries']}")
    print(f"Pattern distribution: {analysis['pattern_distribution']}")
    print(f"\nEngine coverage: {analysis['coverage_rate']}")
    print(f"  Covered: {analysis['covered_count']}")
    print(f"  Uncovered: {analysis['uncovered_count']}")
    print(f"\nUncovered discoveries:")
    for d in analysis["uncovered_discoveries"]:
        print(f"  {d['id']}: {d['discovery']} ({d['pattern']})")
    print(f"\nSaved: {output}")
    return analysis

if __name__ == "__main__":
    analyze_discoveries()
