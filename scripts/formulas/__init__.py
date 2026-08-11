"""
Formula library for DR-7 (formula execution).

Each formula is a callable Python function that takes the stated inputs
and returns the computed output. The verifier (verify_formulas.py)
calls these functions and diffs against the package's stated output.

This is the Layer 2 of the causal graph architecture:
  Layer 0: Raw corpus (patents, papers)
  Layer 1: Edge extractor (mechanisms → edges, ASSERTED)
  Layer 2: Formula verifier (execute formulas, promote ASSERTED → VERIFIED)  ← THIS
  Layer 3: Causal simulator (propagate through VERIFIED edges)
  Layer 4: Experiment designer
  Layer 5: Closed-loop tracker
  Layer 6: Package generator
"""
