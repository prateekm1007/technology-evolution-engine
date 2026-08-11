#!/usr/bin/env python3
"""
goal_parser.py — DR-70: Parse natural-language goals into structured objects.

Parses goals like:
  - "increase efficiency by 20%"
  - "reduce cost by $50/kg"
  - "improve ZT to 1.5"
  - "halve thermal conductivity"
  - "double the Seebeck coefficient"
  - "keep mass below 1 kg"

Each goal becomes a Goal object with:
  - metric (the parameter name)
  - direction (increase/decrease/achieve)
  - magnitude (the relative or absolute change)
  - baseline (the starting value, if known)
  - target (the target value, if derivable)
  - units

Usage:
    from scripts.goal_parser import GoalParser
    gp = GoalParser()
    goal = gp.parse("increase efficiency by 20%", baseline=0.35)
    # goal.metric == "efficiency"
    # goal.direction == "increase"
    # goal.magnitude == 0.20 (relative)
    # goal.target == 0.42
"""
import sys
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class Goal:
    """A structured goal parsed from natural language."""
    raw_text: str
    metric: str                # e.g., "efficiency", "ZT", "cost_per_kg"
    direction: str             # "increase", "decrease", "achieve"
    magnitude_kind: str        # "relative" (fraction) or "absolute" (units)
    magnitude: Optional[float] # the magnitude (fraction or absolute)
    target: Optional[float]    # the target value (if derivable)
    baseline: Optional[float]  # the baseline value (if provided)
    units: str = ""            # e.g., "%", "USD/kg", "V/K"
    confidence: float = 1.0    # 0-1, how confident the parse is

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "metric": self.metric,
            "direction": self.direction,
            "magnitude_kind": self.magnitude_kind,
            "magnitude": self.magnitude,
            "target": self.target,
            "baseline": self.baseline,
            "units": self.units,
            "confidence": self.confidence,
        }


@dataclass
class GoalParseResult:
    """The output of GoalParser.parse_many()."""
    goals: List[Goal] = field(default_factory=list)
    n_goals: int = 0
    unparsed: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goals": [g.to_dict() for g in self.goals],
            "n_goals": self.n_goals,
            "unparsed": self.unparsed,
            "timestamp": self.timestamp,
        }


# Direction keywords → direction.
DIRECTION_KEYWORDS = {
    "increase": ["increase", "improve", "raise", "boost", "enhance",
                 "grow", "amplify", "double", "triple", "quadruple",
                 "maximize"],
    "decrease": ["decrease", "reduce", "lower", "cut", "shrink",
                 "minimize", "halve", "slash"],
    "achieve":  ["achieve", "reach", "attain", "set", "keep",
                 "maintain", "target"],
}

# Metric synonyms → canonical metric name.
METRIC_SYNONYMS = {
    "efficiency": "efficiency",
    "η": "efficiency",
    "power": "power",
    "power_density": "power_density",
    "energy_density": "energy_density",
    "zt": "ZT",
    "figure of merit": "ZT",
    "seebeck": "seebeck_coefficient",
    "seebeck coefficient": "seebeck_coefficient",
    "conductivity": "electrical_conductivity",
    "electrical conductivity": "electrical_conductivity",
    "thermal conductivity": "thermal_conductivity",
    "kappa": "thermal_conductivity",
    "cost": "cost_per_kg",
    "price": "cost_per_kg",
    "weight": "mass",
    "mass": "mass",
    "volume": "volume",
    "capacity": "capacity",
    "capacitance": "capacitance",
    "emissivity": "emissivity",
    "voltage": "voltage",
    "current": "current",
    "lifetime": "lifetime",
    "stability": "stability",
    "durability": "durability",
}


class GoalParser:
    """DR-70: parse natural-language goals into structured objects."""

    # ----- public API ---------------------------------------------------
    def parse(self, text: str, baseline: Optional[float] = None) -> Goal:
        """Parse a single goal from natural-language text.

        Args:
            text: the goal statement
            baseline: optional baseline value for the metric

        Returns:
            A Goal object. If parsing fails, the metric will be the raw
            text and confidence will be low.
        """
        text_lower = text.lower().strip()
        # Identify direction
        direction = "achieve"  # default
        for d, keywords in DIRECTION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                direction = d
                break

        # Identify metric
        metric = self._find_metric(text_lower)

        # Identify magnitude
        mag_kind, magnitude, units = self._find_magnitude(text_lower, direction)

        # Compute target if possible
        target = None
        if baseline is not None and magnitude is not None:
            if direction == "increase" and mag_kind == "relative":
                target = baseline * (1.0 + magnitude)
            elif direction == "decrease" and mag_kind == "relative":
                target = baseline * (1.0 - magnitude)
            elif direction in ("increase", "decrease") and mag_kind == "absolute":
                if direction == "increase":
                    target = baseline + magnitude
                else:
                    target = baseline - magnitude
        # Direct "to X" target overrides
        to_match = re.search(r"\bto\s+(\d+\.?\d*)\s*([a-z/%·]*)", text_lower)
        if to_match:
            target = float(to_match.group(1))
            if not units and to_match.group(2):
                units = to_match.group(2)
            mag_kind = "absolute"

        # Special multipliers
        if "double" in text_lower and baseline is not None:
            target = baseline * 2.0
            mag_kind = "relative"
            magnitude = 1.0
        elif "halve" in text_lower and baseline is not None:
            target = baseline * 0.5
            mag_kind = "relative"
            magnitude = 0.5

        # Confidence
        confidence = 1.0 if metric != text_lower and (magnitude is not None
                                                       or target is not None) else 0.3

        return Goal(
            raw_text=text,
            metric=metric,
            direction=direction,
            magnitude_kind=mag_kind,
            magnitude=magnitude,
            target=target,
            baseline=baseline,
            units=units,
            confidence=confidence,
        )

    def parse_many(self, texts: List[str],
                   baselines: Optional[Dict[str, float]] = None) -> GoalParseResult:
        """Parse a list of goal statements."""
        baselines = baselines or {}
        goals: List[Goal] = []
        unparsed: List[str] = []
        for t in texts:
            g = self.parse(t, baseline=baselines.get(t))
            if g.confidence < 0.5:
                unparsed.append(t)
            else:
                goals.append(g)
        return GoalParseResult(
            goals=goals,
            n_goals=len(goals),
            unparsed=unparsed,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ----- internals ----------------------------------------------------
    def _find_metric(self, text_lower: str) -> str:
        for syn, canonical in METRIC_SYNONYMS.items():
            # Use word-boundary-ish matching (synonyms may contain spaces)
            if syn in text_lower:
                return canonical
        return text_lower  # fallback

    def _find_magnitude(self, text_lower: str,
                        direction: str) -> Tuple[str, Optional[float], str]:
        # Percentage form: "by 20%"
        m = re.search(r"by\s+(\d+\.?\d*)\s*%", text_lower)
        if m:
            return "relative", float(m.group(1)) / 100.0, "%"

        # Currency form: "by $50/kg"
        m = re.search(r"by\s+\$?(\d+\.?\d*)\s*/\s*(\w+)", text_lower)
        if m:
            return "absolute", float(m.group(1)), f"USD/{m.group(2)}"

        # Absolute form: "by 0.05"
        m = re.search(r"by\s+(\d+\.?\d*)\s*([a-z/%·]*)", text_lower)
        if m:
            return "absolute", float(m.group(1)), m.group(2)

        # "to <value> <unit>"
        m = re.search(r"\bto\s+(\d+\.?\d*)", text_lower)
        if m:
            return "absolute", float(m.group(1)), ""

        return "absolute", None, ""


def main():
    print("=" * 60)
    print("GOAL PARSER (DR-70)")
    print("=" * 60)
    print()

    gp = GoalParser()

    examples = [
        ("increase efficiency by 20%", 0.35),
        ("reduce cost by $50/kg", 200.0),
        ("improve ZT to 1.5", None),
        ("halve thermal conductivity", 1.5),
        ("double the Seebeck coefficient", 200e-6),
        ("keep mass below 1 kg", None),
    ]
    for text, baseline in examples:
        g = gp.parse(text, baseline=baseline)
        print(f"  '{text}'  (baseline={baseline})")
        print(f"    → metric={g.metric} dir={g.direction} "
              f"mag_kind={g.magnitude_kind} mag={g.magnitude} "
              f"target={g.target} units='{g.units}' conf={g.confidence:.2f}")
        print()


if __name__ == "__main__":
    main()
