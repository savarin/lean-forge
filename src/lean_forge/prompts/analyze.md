# Phase 0: Analysis

> Center of gravity: **harness quality** — the invariants you identify and
> the prepare.py you write determine the ceiling for the entire optimization.
> A bad harness corrupts every iteration that follows.

Do this ONCE. This is research, not optimization.

Read `$PROMPTS/metric.md` now. It defines the metric and how to identify invariants.

---

## 0.1 Explore the repo

Read source files. For small repos (< 2K lines): read everything.
For large repos: read key modules, entry points, type definitions,
test suites, and any CLAUDE.md / README.md.

**Assess complexity.** Before identifying invariants, classify the repo:

- **Single-module** (< 2K lines, one package): invariants are textbook
  (scope, arity, type safety). Code reading finds them all. Proceed to 0.2.
- **Multi-module** (2K+ lines, multiple packages or services): the most
  dangerous invariants live BETWEEN modules — shared contracts, data format
  assumptions, implicit ordering. Trace the import graph and data flow
  across module boundaries before looking within modules.

## 0.1b Formalize (default — skip if $DIRECT_MODE)

Read `$PROMPTS/formalize.md` now. It guides Lean formalization of the
repo's core types and contracts to surface invariants that code reading
misses. Return here when formalization is complete.

## 0.2 Identify invariants

If formalization was performed (step 0.1b), read `$WORK/findings.md`
now. Merge those invariants with what you found by reading the code.
Formalization-discovered invariants often score 0 (unguarded) or 1
(convention) — these are high-value targets for the optimization loop.

Using the categories from `metric.md`, identify **5–15 critical invariants**
(for repos over 10K lines, aim for the upper end: 12–15).
For each, classify its current enforcement level (structural / validated /
convention / unguarded).

**Priority: invisible when broken.** The most valuable invariants are those
where violation doesn't crash — the system still serves, still renders, still
computes, but produces wrong results. These are the ones code reading misses
because nothing visibly fails. Rank by:
1. Silent corruption (wrong results, not crashes)
2. Invisible at the call site (caller can't see the risk)
3. Affects downstream consumers (data flows, API contracts)

**For multi-module repos:** After within-module invariants, explicitly search
for cross-module invariants:
- What does module A assume about module B's output format?
- Are there shared type definitions, or does each module define its own?
- Do two modules agree on ordering, encoding, or error conventions?
- Is there a contract that crosses a package boundary without a shared type?

Cross-module invariants are often convention (1) or unguarded (0) because
each module was written to its own spec, not to a shared contract.

## 0.3 Write the evaluation harness

Create `$WORK/prepare.py` following the template in `metric.md`.
Each invariant gets a check function that examines the source code and
returns `(score, explanation)`. The harness prints a scorecard and
grep-extractable metrics.

Run it. Record the baseline IES.

**Validate the harness.** Compare prepare.py's output to your manual assessment
from step 0.2. For each invariant, check: does the score match what you found
by reading the code? If any score is wrong, fix the check function NOW.
The harness is the foundation — a bad harness corrupts the entire loop.

**Check the score distribution.** After validation, review:
- Invariants should span at least **3 different categories** from metric.md
  (e.g., type safety, input validation, contract consistency). If all
  invariants are the same category, you're missing critical areas — re-read
  the codebase focusing on uncovered categories.
- If >80% of invariants score the same level, the harness may be too lenient
  (all 2s) or too strict (all 0s). Re-examine the check functions.

**Robustness check.** For each check function, simulate a reasonable
implementation variant: multiline raise, guard clause on a separate line,
return type on the next line, renamed variable. Would the regex still
detect it? If not, make the check more robust NOW — you cannot fix
prepare.py after freezing. Prefer `re.DOTALL` with scope extraction
over single-line patterns.

**Compute the theoretical maximum (hard gate).** Before freezing, trace
every `return` statement in each check function. Build this table and
include it in targets.md:

| Check function | Max returnable score | What triggers score 3 |
|---|---|---|
| check_01_... | 3 | <detection pattern that returns 3> |
| check_02_... | 3 | <detection pattern> |

Most check functions MUST have a return path that returns score 3.
For invariants where structural enforcement is architecturally
inappropriate (e.g., cross-module contracts where a shared type would
be over-engineering), a max of 2 is acceptable — mark these as
"validated-ceiling" in the table with a one-line reason. No more than
2 invariants may have a validated ceiling.

Theoretical max = Σ(max_score) / (3 × N). **This must be >= 0.90.**
If it's lower, add score-3 detection paths before freezing.

**Verify mechanically:**
```bash
grep -cE 'return\s+\(?3,' $WORK/prepare.py
```
This count should be >= N-2 (where N is the number of check functions).
If it's lower, fix the harness before proceeding.

## 0.4 Freeze the evaluation harness

After validating prepare.py, lock it:
```bash
shasum -a 256 $WORK/prepare.py > $WORK/prepare.py.sha256
```

From this point forward, **prepare.py is FROZEN**. Do not modify it during
Phase 1 or Phase 2. If you discover a check is wrong mid-loop, note it in
ideas.md — that's a Harness ceiling stop condition, not a reason to edit
the harness.

## 0.5 Write the improvement plan

Create `$WORK/targets.md`:

```markdown
# Improvement Targets

Baseline IES: X.XX (N/M)
Theoretical max IES: X.XX

## Strategic assessment

<1-3 sentences: Where does this repo's risk concentrate? What category
of invariant is most likely to yield improvements? What's the repo's
hidden-invariant density — are the dangerous invariants obvious from
code reading, or do they hide in module boundaries and implicit contracts?>

## Phase 1 targets (execute sequentially)

### Target 1: <invariant name> (<current_score>→<target_score>)
**Invariant:** <what must be true>
**Category:** <type safety | input validation | contract consistency | ...>
**Strategy:** <structural | validated>
**Where:** <how to find the right place — grep pattern, not line number>
**What:** <what check/type/validation to add>
**Test:** <what test to write>

### Target 2: ...
...

## Phase 2 ideas (explore after Phase 1)
- Idea A: ...
- Idea B: ...
```

Order targets by: score gain / implementation complexity. Easiest wins first.

**Simplicity criterion:** Prefer validated (score 2) adding 3 lines over
structural (score 3) adding 50 lines of type machinery. The cheapest
improvement that reaches the target score wins.

**Structural attempt:** For at least ONE target, attempt structural
enforcement (score 3) before falling back to validated. Use the repo's
existing type system — NewType, frozen dataclasses, enums, Protocol.
If the structural approach adds >30 lines, fall back to validated.

## 0.6 Initialize

```bash
git -C $REPO checkout lean-forge/$TAG 2>/dev/null || git -C $REPO checkout -b lean-forge/$TAG
```

**Check for prior run.** If `$WORK/results.tsv` already exists, a prior run
used this tag. Stop and tell the user: "Tag `$TAG` already has results.
Use `--tag <new-tag>` to start fresh."

```bash
printf "commit\ties_score\tstructural\tvalidated\tconvention\tunguarded\tlines_delta\ttests\tstatus\tdescription\n" > $WORK/results.tsv
printf "# Iteration Log\n" > $WORK/iteration-log.md
```

Create `$WORK/ideas.md`:

```markdown
# Ideas Tracker

## Dead Ends
Approaches tried and abandoned. The WHY matters more than the result.

| Iteration | Approach | Result | Why it failed |
|-----------|----------|--------|---------------|

## Key Insights
Generalizable learnings that should affect all subsequent iterations.

## Remaining Ideas
Prioritized queue. Cross out as you attempt them.

- [ ] <from targets.md Phase 2 ideas>
```

---

Phase 0 is complete. Return to `protocol.md` for Phase 1.
