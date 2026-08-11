# WCP_PROTOCOL

**Status:** World-Class Product Development Protocol.
**Location:** TEE repo root.
**Phase:** WCP-1.

> The bottleneck is no longer coding.
> The bottleneck is now taste, judgment, data quality,
> engineering discipline, and contact with reality.
> — CEO directive, WCP-1

---

## The 15 Principles

### Principle 1 — Study the masters

Before building anything, answer:
- Who solved this problem?
- Who almost solved this problem?
- Who failed?
- Why did they fail?
- What did they know that we do not?

### Principle 2 — Build an adversarial library

Every object receives four companions:
- SUCCESS_LIBRARY (what worked)
- FAILURE_LIBRARY (what failed)
- PATENT_LIBRARY (what is protected)
- REGULATION_LIBRARY (what is required)

### Principle 3 — Create a source hierarchy

| Tier | Source | Weight |
|---|---|---|
| 1 | Physics | 1.00 |
| 2 | Experiments | 0.95 |
| 3 | Standards | 0.95 |
| 4 | Regulations | 0.90 |
| 5 | Patents | 0.90 |
| 6 | Academic literature | 0.85 |
| 7 | Manufacturer documentation | 0.80 |
| 8 | Field reports | 0.70 |
| 9 | User feedback | 0.60 |
| 10 | LLM inference | 0.20 |

### Principle 4 — Study world-class products

For every blueprint, collect:
- Product analysis (specs, dimensions, tolerances, materials, suppliers, patents, pricing, recalls, maintenance)
- Economic analysis (unit economics, margins, capex, opex, distribution, labor)
- User analysis (complaints, reviews, return rates, repair frequency)
- Failure analysis (lawsuits, recalls, incidents, postmortems)

### Principle 5 — Build the cemetery

Maintain both a SUCCESS_GRAPH and a FAILURE_GRAPH.

Failure categories: technical, economic, regulatory, manufacturing,
coordination, maintenance, human-factors, security.

### Principle 6 — Build the trade-off engine

Nothing is free. Everything becomes a trade-off:
- cost, weight, strength, complexity, reliability, maintainability,
  repairability, efficiency

### Principle 7 — Build a world model

The Blueprint understands:
- Physics (thermodynamics, fluid dynamics, electromagnetism, structural mechanics)
- Economics (cost curves, supply chains, market structure, capital costs)
- Manufacturing (machining, molding, welding, casting, assembly)
- Regulation (standards, certification, liability)
- Human factors (ergonomics, safety, usability, training)

### Principle 8 — Build a benchmarking engine

For every blueprint:
- Best in class: Who is better?
- Cheapest: Who is cheaper?
- Most reliable: Who fails less?
- Most profitable: Who captures the most value?
- Most scalable: Who operates at the largest scale?

### Principle 9 — Measure everything

Track: build time, failure rate, manufacturing yield, maintenance cost,
operating cost, capital expenditure, return on investment.

### Principle 10 — Fight entropy

Every week, ask:
- What assumptions became false?
- What changed?
- What failed?
- What did we learn?
- What should be removed?

### Principle 11 — Never trust a single source

Every important claim must be supported by:
- an observation
- an independent source
- a contradiction search

### Principle 12 — Build a memory system

Store: assumptions, failures, designs, simulations, alternatives,
decisions, evidence.

### Principle 13 — Study reality continuously

Workflow: observe → decompose → compare → simulate → construct →
test → fail → learn → repeat.

### Principle 14 — Build for the cheapest path to excellence

Maximize: value created / cost incurred.

### Principle 15 — Preserve institutional memory

```text
failure → boundary → classification → mechanism → constraint →
reachability → blueprint
```

That chain is the company's deepest moat.

---

## Status of each principle

| Principle | Status | Where |
|---|---|---|
| 1. Study the masters | PARTIALLY DONE | Evidence Engine Layer 1-2 (5 existing products, 3 failed products studied) |
| 2. Adversarial library | PARTIALLY DONE | Evidence Engine has success/failure evidence; FAILURE_LIBRARY.md exists. Needs structured per-object companions. |
| 3. Source hierarchy | DONE | evidence-engine.ts ranks A-I with weights |
| 4. Study world-class products | PARTIALLY DONE | 5 products studied (John Deere, Naio, FarmWise, DJI, Kubota). Needs deeper analysis. |
| 5. Build the cemetery | PARTIALLY DONE | FAILURE_LIBRARY.md (7 types), failure modes in blueprint. Needs SUCCESS_GRAPH. |
| 6. Trade-off engine | **BUILDING** | New engine in this commit |
| 7. World model | PARTIALLY DONE | Constraint graph (20 nodes, 19 edges), state vector (7 dimensions). Needs physics/economics models. |
| 8. Benchmarking engine | **BUILDING** | New engine in this commit |
| 9. Measure everything | PARTIALLY DONE | Simulation engine (18 metrics). Needs build-time/yield/ROI tracking. |
| 10. Fight entropy | DOCUMENTED | CODER_DIRECTIONS.md weekly review questions. Not yet automated. |
| 11. Never trust single source | NOT DONE | Needs triple-verification protocol in evidence engine. |
| 12. Memory system | PARTIALLY DONE | Versioning (immutable artifacts). Needs design/simulation storage. |
| 13. Study reality continuously | DOCUMENTED | CODER_DIRECTIONS.md workflow. Not yet automated. |
| 14. Cheapest path to excellence | PRINCIPLE | Not yet measured. |
| 15. Preserve institutional memory | DONE | Phases 1-17 + BP-0/BP-1/BP-2 preserved in TEE repo (163 commits). |
