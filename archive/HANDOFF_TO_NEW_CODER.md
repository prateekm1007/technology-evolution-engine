# HANDOFF TO NEW CODER — Cycle 135+ (Revised after git fetch)

**Generated:** 2026-08-06, cycle 134 (auditor), revised after discovering the local clone was stale
**For:** The coder who takes over from cycle 135
**Remote state:** `origin/main` at `3e732d1` (cycle 129 — F-067 retraction)
**Actual gap:** Cycles 130-133 were done locally but never pushed

---

## 0. What Happened (The F-071 Story — Three Reclassifications)

F-071 went through three reclassifications as the real root cause emerged:

1. **Original (cycle 134 start):** The auditor claimed cycles 129-133 work "doesn't exist on disk." This was true for the local clone — but the clone was stale (commit `6ec0980`, cycle ~30).
2. **Reclassification 1 (CEO input):** "The coder didn't push." Partially wrong — the coder pushed cycles 43-129 (111 commits, 39,216 lines).
3. **Reclassification 2 (after `git fetch`):** The auditor never fetched the remote. The local clone was 111 commits behind. Most claimed work EXISTS on `origin/main`. Only cycles 130-133 are the actual unpushed gap.

**The real lesson:** Before verifying any claim against "the disk," run `git fetch origin`. The local working copy is not the source of truth — the remote is. The auditor's entire cycle-134 audit PDF was based on a stale clone and is itself now unreliable.

---

## 1. The Real State (After `git fetch && git reset --hard origin/main`)

### 1.1 Git state
- **Remote:** `https://github.com/prateekm1007/technology-evolution-engine.git`
- **Branch:** `main` at `3e732d1` (cycle 129 — "fix(F-067): retract cycle-128 scorecard")
- **Commits:** 111 commits beyond the old stale clone (cycles 43-129)
- **Last commit message:** "fix(F-067): retract cycle-128 scorecard — honest numbers from actual code"

### 1.2 What EXISTS on the remote (verified after fetch)
- `EPISTEMIC_ENGINE.md` — EXISTS (the governance doc with DR-31..DR-34 and adversarial validation rules)
- `scripts/nine_tenths_loop.py` — EXISTS (the 9/10 scoring driver)
- `scripts/epistemic_pipeline.py` — EXISTS (the 7-step pipeline)
- `scripts/reaudit_loop.py` — EXISTS (Gen 6 re-audit)
- `invention_compiler/discovery_graph.py` — EXISTS (6-layer discovery graph)
- `invention_compiler/bacon_engine.py` — EXISTS (BACON定律发现 engine)
- `scripts/nlp_pipeline.py` — EXISTS (GLiREL/GLiNER references present)
- **81 test files** (not 43, not 96)
- **24 DRs** in MASTER_PROTOCOL.md (DR-1 through DR-24)
- **F-062 through F-067** in FAILURES.md

### 1.3 What does NOT exist (the actual unpushed gap — cycles 130-133)
These were done locally (per worklog entries) but never committed or pushed:
- `scripts/calibration.py` — the 595-line Platt/isotonic implementation
- `benchmarks/relation_extraction_benchmark.py` — the Gen 3 F1 benchmark (claimed F1=0.029→0.298)
- `benchmarks/entity_extraction_benchmark.py` — Gen 2 F1 benchmark (claimed F1=0.695)
- `benchmarks/section_segmentation_benchmark.py` — Gen 1 F1 benchmark (claimed F1=1.000)
- `benchmarks/mechanism_chain_benchmark.py` — Gen 4 F1 benchmark
- F-068, F-069, F-070 in FAILURES.md
- DR-25 through DR-49 in MASTER_PROTOCOL.md

### 1.4 Honest scorecard (from F-067 retraction, cycle 129)
The cycle-128 "ALL SIX GENERATIONS AT 9/10" was retracted in cycle 129 (F-067). The honest cycle-129 scorecard:
- Gen 1: 7/10 (infrastructure only)
- Gen 2: 8/10
- Gen 3: 5/10 (bottleneck — pattern-based, "NOT NLP")
- Gen 4: 7/10
- Gen 5: 7/10 (was missing from cycle-128, now scored)
- Gen 6: 9/10 (but GEN6-VERIFY flagged vocabulary_hash issues)
- Calibration: 7/10 (ECE cap not yet implemented)
- **At 9/10 target: ~1/7** (Gen 6, pending vocabulary_hash fix verification)

Cycles 130-133 (unpushed) claimed to improve this to 2/7, but those claims are unverifiable without the code.

---

## 2. Governance Files You MUST Read

**Read these from disk (after `git pull`) before writing any code.** Run `bash /home/z/my-project/scripts/read_governance.sh` for a disk-verified read receipt with SHA-256 hashes.

### Tier 1 — Constitutional (read first)
| File | Key contents |
|---|---|
| `CONSTITUTION.md` | 8 Laws (Law 7: historical permanence; Law 8: verification standard), Governing Principle ("prefer uncomfortable truth to elegant theory") |
| `MASTER_PROTOCOL.md` | 14 Laws + 11 APs + 26 PRs + **24 DRs** (DR-1 through DR-24). Key: DR-3 (no benchmark grades itself), DR-11 (causal graph), DR-15 (three-tier edge schema), DR-18 (experiment selection) |
| `ANTI_ENTROPY.md` | P1-P70 principles. Key: P1 (claim not true until executed), P10 (write down why a bug was missed), P27 (read the assertion not the test name) |
| `EPISTEMIC_ENGINE.md` | Adversarial validation spec (DR-31..DR-34 on remote). §0 core principle ("every claim must remain vulnerable to attack") |

### Tier 2 — Failure record
| File | Key entries |
|---|---|
| `FAILURES.md` | F-001 through F-067 (real entries) + F-071 (this cycle, reclassified twice). **Read F-067 carefully** — it's the cycle-129 retraction and shows the pattern of "scorecard produced outside committed code." |

### Tier 3 — Contributing
| File | What it is |
|---|---|
| `CONTRIBUTING.md` | Commit discipline, pre-commit hooks |
| `EXAMPLE_BLUEPRINT_001.md` | Reference output format |

### Worklog
`/home/z/my-project/worklog.md` — shared multi-agent log. Cycles 31-132 have entries but **cycles 129-132 describe work that may not match the remote state** (the auditor didn't fetch). Always cross-reference worklog claims against `git log origin/main`.

---

## 3. The Push Discipline (DR-19, the fix for F-071)

**Proposed DR-19:** No worklog entry, audit PDF, scorecard, or "done" statement may claim work is complete unless the files are committed AND pushed AND fetched. The worklog indexes the remote, not any local copy.

**Your operational rule:**
1. Write code/test/governance.
2. `git add <specific files>` (never `-A` — there are 729 spurious mode-only changes from extraction).
3. `git commit -m "<type>(<scope>): <subject>"`.
4. `git push origin main`.
5. `git fetch origin && git log --oneline origin/main` — verify your commit is there.
6. Only NOW may you write a worklog entry claiming the work is done.

**Before every session:** `git fetch origin && git pull origin main` — ensure your local copy is current. F-071 happened because the auditor skipped this step.

---

## 4. What's Done (On Remote, Verified)

1. **Cycles 43-129** — 111 commits of real work (BACON定律发现, reaudit loop, 6-generation pipeline, blind tests, Gentner analogy, dimensional reasoning, etc.)
2. **F-067 retraction** — cycle-128 scorecard honestly retracted (the "ALL SIX AT 9/10" was fabricated outside committed code)
3. **81 test files** — substantial test suite
4. **24 DRs** — governance through DR-24
5. **EPISTEMIC_ENGINE.md** — adversarial validation spec
6. **6-generation pipeline** — epistemic_pipeline.py, nine_tenths_loop.py, reaudit_loop.py
7. **BACON engine** — discovered Stefan-Boltzmann from data
8. **Discovery graph** — 6-layer model
9. **3 confirmed discoveries** — mycelium→biomineralization, nanofiber↔BBB, chitin→magnetic storage

---

## 5. What's Left (Cycle 135+ Roadmap)

### 5.1 Recover cycles 130-133 (if the previous coder's local disk is accessible)
The unpushed work (§1.3) may be recoverable. If so, commit and push it. **Verify each file against the worklog claims before pushing.**

### 5.2 If not recoverable, rebuild in this order
1. **`scripts/calibration.py`** — Platt/isotonic calibration (F-067 blocker #4). The remote has `web/backend/adapters/calibration.py` (basic CalibrationStore) but not the 595-line implementation.
2. **`benchmarks/relation_extraction_benchmark.py`** — Gen 3 P/R benchmark. The F-067 retraction showed Gen 3 is the bottleneck (5/10, pattern-based). Measure the real F1 first, then improve.
3. **F-068** (CALIB-SCORE-DESIGN) — log in FAILURES.md, then fix with ECE cap.
4. **DR-25+** — add to MASTER_PROTOCOL.md as needed (DR-49 "outcome quality gate" was proposed but never landed on remote).
5. **Gen 6 vocabulary_hash fix** — F-067 blocker #6 (66% of reaudit entries have empty hash).

### 5.3 The CEO's 9/10 directive
Honest baseline: ~1/7 at target (Gen 6, pending vocabulary_hash verification). Path: measure (benchmark) → improve (code) → re-measure → push → worklog. No score may rise without a measured outcome.

---

## 6. Autocommands (Nothing Manual)

All scripts at `/home/z/my-project/scripts/` (already written, executable):

| Script | Purpose |
|---|---|
| `setup.sh` | One-time env setup (clone, venv, deps, pytest collection) |
| `verify_env.sh` | Pre-push verification (CI gates + test collection) |
| `push_work.sh "<msg>" [files]` | Disciplined push (verify → add specific → commit → push → verify on origin) |
| `run_tests.sh` | Full test suite |
| `read_governance.sh` | Disk-verified read receipt with SHA-256 hashes |
| `audit_disk_state.sh` | Verify what exists vs what's claimed (now includes `git fetch` check) |

**Day-one pre-flight:**
```bash
bash /home/z/my-project/scripts/setup.sh
bash /home/z/my-project/scripts/read_governance.sh
bash /home/z/my-project/scripts/audit_disk_state.sh
cd /home/z/my-project/audit/technology-evolution-engine && git fetch origin && git pull origin main
bash /home/z/my-project/scripts/run_tests.sh
```

---

## 7. Anti-Entropy File Structure Rules

1. **Scripts** (runnable, `if __name__ == "__main__"`) → `scripts/`
2. **Importable modules** → `product/`, `invention_compiler/`, `engine/`, `loops/`
3. **Tests** (`test_*.py`) → `tests/`
4. **Benchmarks** → `benchmarks/<type>/input|expected|outputs|reports/`
5. **Governance docs** → repo root (`EPISTEMIC_ENGINE.md` alongside `MASTER_PROTOCOL.md`)
6. **Never** create `_new`/`_fixed`/`_final`/`_latest` variants (CONSTITUTION entropy rule)
7. **`archive/`** is frozen — read-only
8. **PDFs** → `download/` (only user-downloadable directory)
9. **Worklog** → `/home/z/my-project/worklog.md` (outside repo, shared, append-only)

---

## 8. Communication Protocol With CEO

1. **Read governance from disk every session** — paste `read_governance.sh` output as your read receipt.
2. **Fetch before you verify** — `git fetch origin` is the first command of every session. F-071 happened because this was skipped.
3. **Push before you claim** — use `push_work.sh`. The CEO verifies against `origin/main`, not your local disk.
4. **When the CEO catches an error, acknowledge and fix the root cause.** F-067 and F-071 both made the project stronger.
5. **Honesty over elegance.** If your benchmark returns F1=0.03, report F1=0.03.

---

## 9. Closing

The previous coder did real work (cycles 43-129, on remote). A later session did cycles 130-133 locally but didn't push. The auditor (cycle 134) verified against a stale clone and never fetched, producing F-071 — which itself had to be reclassified twice as the real root cause emerged.

The lessons, in order:
1. **Fetch before you verify.** The remote is the source of truth.
2. **Push before you claim.** Unverified local work is unverified work.
3. **The auditor is not exempt from the auditor's rules.** Verify against the remote, not the local clone.

Welcome to cycle 135. Start by fetching.
