# BP0_RECORD — Blueprint Zero

**Status:** Product record (BP-0 built on top of Phase 17 foundation).
**Location:** TEE repo root.
**Date:** 2026-08-02.

> This is the point where a laboratory becomes a company.
> — CEO directive, Phase 18 (Blueprint Zero)

---

## What BP-0 is

Blueprint Zero (BP-0) is a working Next.js web application that
transforms an idea input into a complete, executable blueprint.
It is the first deliverable in the project's history that is
*executable code* rather than a document.

BP-0 was built in a separate Next.js project environment
(`/home/z/my-project/src/`), not by modifying this TEE research
repo. The TEE repo (Phases 1-17) is the foundation; BP-0 is the
product built on top of it.

## What BP-0 does

Input: "Build a solar-powered irrigation robot for small farms in India."

Output: a complete Reachability Report containing:
- Classification (RECOMBINATION dominant, EMERGENCE secondary)
- 7-dimensional state vector
- 9 constraints with severity/probability/mitigation
- Dependency graph with critical path
- 16-item BOM with real prices from named suppliers ($2,373 total)
- Cost model ($1.2M capital, $3K unit cost, 3.3-year break-even)
- CAD specification (dimensions, materials, tolerances, joints)
- Manufacturing plan (14 assembly steps, 6h/unit, 92% yield)
- Regulatory pathway (India, US, EU with risk assessments)
- Deployment plan (3 phases over 36 months, staffing, budget)
- Failure analysis (7 failure modes, risk 0.4, highest: economic)

## What BP-0 uses from this repo

BP-0 transcribes the following Phase 17 deliverables into its
`src/lib/blueprint-data.ts`:
- COMPONENT_LIBRARY.md (13 components with real specs and prices)
- MATERIAL_LIBRARY.md (7 materials with real properties)
- SUPPLIER_LIBRARY.md (20 suppliers with real cost/lead/reliability)
- EXAMPLE_BLUEPRINT_001.md (the solar irrigation robot reference)

The frozen formula (FORMULA_B_FROZEN.md, INST-001) is preserved
and not modified. BP-0 uses the full Blueprint Engine architecture
(Phase 16A), not just the frozen formula.

## Restrictions honored

- Autonomous agricultural systems ONLY (per BP-0 directive)
- No aerospace, pharma, semiconductors, automobiles, or multi-domain
- Phase 5 baseline unchanged (graph v4.2, 669 nodes)
- No prior phase work deleted (Rule 1)
- No engine or test code in this repo modified

## Audit status

Per external audit (commit `47f8395` audit cycle):
- CC1: preview link live, API works — VERIFIED
- CC2: BOM has real suppliers/prices — VERIFIED
- CC3: domain restriction enforced — VERIFIED
- CC4: TEE repo preserved — VERIFIED
- CC5: no operational code in TEE — VERIFIED
- CC6: success criterion — PARTIALLY MET (evaluation-ready, not production-ready)
- CC7: Complete tool called — VERIFIED
- CC9: TEE worklog not updated — NEW P3 (this record closes the gap)

## What BP-0 does NOT do

- It does not add the missing items from the Phase 17 falsifier
  (BB4): detailed wiring harness, ROS2 software architecture,
  irrigation valve specifications, firmware for MCU. BP-0 inherits
  these gaps. A manufacturer would need to design these before
  production could begin.
- It does not support multiple domains. Only autonomous agricultural
  systems.
- It does not modify the frozen formula or any prior architecture.

## Where BP-0 lives

- Source code: `/home/z/my-project/src/` (Next.js project, separate from TEE repo)
- Preview: https://preview-chat-651cecea-9dab-4521-8ce9-5c59cd7b570a.space-z.ai/
- API: POST `/api/compile` with `{"idea": "..."}`

This record is committed to the TEE repo so the repo's history
reflects that BP-0 was built on top of it. The TEE repo remains
the research foundation; BP-0 is the product.
