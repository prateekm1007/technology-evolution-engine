"""
Invention Compiler — Top-level package.

This package implements the directive in INVENTION_COMPILER.md:
the system is an invention compiler, not an idea generator. Every
invention emitted by the compiler must produce all 11 layers, from
Layer 0 (Opportunity definition) through Layer 10 (Final blueprint).

Module-to-layer mapping (per INVENTION_COMPILER.md):

  Layer 0  — OpportunityDefinition (this orchestrator) + analogy_engine
  Layer 1  — physics_engine, chemistry_engine, biology_engine,
              mathematics_engine, economics_engine
  Layer 2  — dependency_engine, resurrection_engine
  Layer 3  — mathematics_engine, constraint_engine
  Layer 4  — constraint_engine (subsystems/tolerances)
  Layer 5  — simulation_engine
  Layer 6  — constraint_engine (materials/suppliers/tooling)
  Layer 7  — economics_engine
  Layer 8  — verification_engine (proposes hypothesis + experiments)
  Layer 9  — prototype_engine
  Layer 10 — blueprint_engine

Law 8 honesty rule (per ANTI_ENTROPY.md): every layer that emits a
scalar must also emit:
  - evidence: the inputs that produced the scalar
  - assumptions: what the scalar assumes
  - falsification_criteria: what would prove the scalar wrong
"""
