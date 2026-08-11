# Claims NOT Being Made

The following statements are explicitly prohibited. No document in this repository should make any of these claims:

```
"The engine has demonstrated independent invention."
"Gen5 has achieved X% discovery."
"Discovery F1 = 0.5714."
"The engine has 57% discovery capability."
"Precision is 100%."
"The benchmark proves genuine invention."
"H1–H4 are experimentally established."
"DSL saturation has been demonstrated."
```

## Why these claims are prohibited

The frozen benchmark result (F1=0.5714) is retained as historical evidence only. Stage −1 established that it cannot support independent-discovery claims because:

1. **25% of TPs come from ambient entity presence**, not from the system proposing the bridge. The scorer does not require proposal.

2. **FP=0 by construction**. The scorer never counts false positives. Precision=1.0 is a tautology, not a measurement. The actual proposal-level precision is 0.2727 (6/22).

3. **Zero strict-normalized matches exist**. All 20 current matches are token-overlap or substring. The matcher is granting lexical credit, not proving semantic relationships.

4. **The shuffled-gold null hit rate is 0.1374**. Random gold assignment produces matches 13.7% of the time. The current 40% hit rate is above this floor, but the gap is not sufficient to establish independent discovery given the other defects.

## What IS being claimed

- The repository contains a measurement infrastructure that is now honest about its own limitations.
- The Stage −1 metrology provides a complete picture of what the current scorer measures and what it does not.
- The frozen baseline is evidence of a measurement defect, not evidence of discovery capability.
- The repository is awaiting independent external review to determine whether genuine discovery is possible.

## The correct posture

**Current benchmark → invalid for independent discovery → frozen baseline → repair methodology → independently rerun.**

No one should describe F1=0.5714 as "the system's discovery capability." It is a historical result under a scoring methodology that has been measured and found invalid for independent-discovery claims.
