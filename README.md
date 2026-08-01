# Technology Evolution Engine (TEE)

> Given the present state of civilization, what should exist but does not,
> why it does not, what must change, and how confidently we can predict its arrival.

## Purpose

The TEE is an automated institution for technology foresight.
It does not generate ideas. It determines:

1. What transformations are blocked
2. Which constraints prevent them
3. What prerequisites are missing
4. When those prerequisites become available
5. How confidently we can predict arrival

## Architecture

See CONSTITUTION.md for the frozen architecture and eight constitutional laws.
See HANDOFF.md for the master handoff document.

## Metrics

- PCS: Prerequisite Completion Score
- RPS: Resurrection Probability Score
- CIS: Combinatorial Innovation Score
- TFS: Technology Foresight Score

## Rules

- Everything is automated. No manual editing.
- Architecture is frozen. No new agents without evidence.
- The graph is canonical. Documents are representations.
- Every candidate must survive adversarial attack.

## Setup

```bash
pip install -r requirements.txt
pre-commit install   # wires the governance loop as a git hook
```

The `pre-commit install` step is mandatory. It wires
`scripts/remember_governance.py` as a pre-commit hook that checks
all 6 governor files (CONSTITUTION.md, INVENTION_COMPILER.md,
ANTI_ENTROPY.md, CONTRIBUTING.md, FAILURES.md, HANDOFF.md) are
present before every commit. Without this step, the governance loop
is configured but not enforced.

See CONTRIBUTING.md for the pre-commit checklist (10 session-hardened
principles distilled from actual failures).

## License

Private. All rights reserved.