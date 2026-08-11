# MECHANISM_STATUS.md

## Mechanism classification status (DR-42)

### Status classes

```text
associative           — co-occurrence without causal evidence
asserted              — described in text but not verified
plausibility-checked  — passes basic plausibility constraints
verified              — confirmed by measurement or external source
contradicted          — refuted by measurement or external source
```

### Weakest-link rule

A mechanism chain's status is the WEAKEST status of any edge in the chain:
- If any edge is `contradicted`, the chain is `contradicted`
- If any edge is `associative`, the chain is `associative`
- Otherwise, the chain takes the minimum status of its edges

### Promotion rules

```text
associative → asserted        : requires text span evidence
asserted → plausibility-checked: passes constraint check
plausibility-checked → verified: requires measurement or external source
verified → contradicted       : requires refuting measurement
```

### Forbidden

- Contradicted chains promoted to verified
- Verified edges without provenance
- Status changes without evidence

### PASS criteria

- Chain scoring passes (weakest-link enforced)
- Contradiction propagation passes (contradicted edges invalidate chains)
