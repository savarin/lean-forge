# Optimization Loop Protocol

> Center of gravity: **the keep/discard iteration** — implement, evaluate,
> decide, record. Re-read this file at the start of Phase 1 and reference
> ideas.md every iteration.

Two protocols: **Execute** (for known improvements) and **Explore** (for discovery).
Use Execute first, then switch to Explore when known targets are exhausted.

## Paths

```
WORK=$REPO/.lean-forge
```

All evaluation output goes to `$WORK/`. All code changes go to `$REPO/`.

## Constraints (apply to BOTH protocols)

- **No new dependencies.** Do not add entries to requirements.txt,
  pyproject.toml dependencies, package.json, Cargo.toml, go.mod, etc.
  Use only stdlib and existing project dependencies.
- **Do NOT modify prepare.py.** The harness is frozen after Phase 0.
  If you believe a check is wrong, note it in ideas.md — do not fix it.
  Verify before each evaluation: `shasum -a 256 -c $WORK/prepare.py.sha256`
- **15-minute iteration timeout.** Note the wall time before starting each
  iteration. If implementation + testing exceeds 15 minutes, discard and
  move on.
- **Simplicity criterion.** When two approaches give the same IES improvement,
  keep the one with fewer lines changed. Prefer validated (2) adding 3 lines
  over structural (3) adding 50 lines of type machinery.

## Execute Protocol

For targets identified in Phase 0 and listed in `$WORK/targets.md`.
These are pre-validated — each is a known-good improvement.

```
FOR EACH target in targets.md:
  1. Read the target specification (invariant, strategy, where, what, test)
  2. Find the right location (grep for the pattern, don't assume line numbers)
  3. Implement the change
  4. Write the test
  5. Commit:
       git -C $REPO add -A && git -C $REPO commit -m "lean-forge: <description>"
  6. Evaluate:
       shasum -a 256 -c $WORK/prepare.py.sha256
       python3 $WORK/prepare.py > $WORK/run.log 2>&1
       grep "^ies_score:" $WORK/run.log
  7. Run tests:
       <test command from $REPO> > $WORK/test.log 2>&1
       tail -5 $WORK/test.log
  8. If tests FAIL:
       - Read the error (tail -30 $WORK/test.log)
       - Fix the implementation (the invariant is correct, the code has a bug)
       - Amend the commit and re-run
       - If 3 fix attempts fail: git -C $REPO reset --hard HEAD~1, add to
         Remaining Ideas in ideas.md (different approach needed), move to
         next target
  9. If prepare.py itself errors (not a score change — an exception):
       Log status=eval_error in results.tsv. This is a stop condition.
       Do NOT attempt to fix prepare.py. Record the error and stop.
  10. Record in $WORK/results.tsv (include lines_delta from git diff --stat).
       The `tests` column: number of test failures (0 = all passed, N = N failed,
       -1 = no test suite found, -2 = test command timed out).
  11. Log the iteration (append to $WORK/iteration-log.md):
       ```
       ## Iteration N: <short title>
       **Hypothesis:** <what you expected to improve and why>
       **Change:** <what you actually did — files, functions, approach>
       **Result:** IES X.XX → Y.YY (<delta>), <lines_delta>. <one sentence: matched expectations or surprised you?>
       ```
  12. Cross out target in $WORK/targets.md
  13. Update $WORK/ideas.md (Key Insights if anything surprised you)
```

**Test command detection:** Check the repo for:
- `pyproject.toml` with `[tool.pytest]` → `uv run pytest -x -q`
- `Makefile` with `test` target → `make test`
- `package.json` with `test` script → `npm test`
- `Cargo.toml` → `cargo test`
- Fall back to: `uv run pytest -x -q` for Python, `go test ./...` for Go

When all targets are done, proceed to the Explore protocol.

## Explore Protocol

For discovering improvements NOT identified in Phase 0.
This is the AUTORESEARCH loop adapted for code hardening.

```
LOOP:
  1. Read $WORK/ideas.md — check Dead Ends, Key Insights, Remaining Ideas
  2. Pick next idea from Remaining Ideas
     Priority: score gain / complexity. Prefer:
       - Unguarded (0) → validated (2): +2 points, usually easy
       - Convention (1) → structural (3): +2 points, may need type changes
       - Validated (2) → structural (3): +1 point, often hard
  3. Implement the change
  4. Commit:
       git -C $REPO add -A && git -C $REPO commit -m "lean-forge: <description>"
  5. Evaluate:
       shasum -a 256 -c $WORK/prepare.py.sha256
       python3 $WORK/prepare.py > $WORK/run.log 2>&1
       grep "^ies_score:" $WORK/run.log
  6. Run tests:
       <test command from $REPO> > $WORK/test.log 2>&1
  7. If prepare.py itself errors: log status=eval_error, stop.
  8. Keep/discard:
       KEEP if: tests pass AND ies_score ≥ previous best
       DISCARD if: tests fail OR ies_score < previous best
         → git -C $REPO reset --hard HEAD~1
  9. Record in $WORK/results.tsv (include lines_delta).
       The `tests` column: number of failures (0 = passed, -1 = no suite).
       - On keep: status=keep
       - On discard: status=discard
  10. Log the iteration (append to $WORK/iteration-log.md):
       ```
       ## Iteration N: <short title> [keep|discard]
       **Hypothesis:** <what you expected to improve and why>
       **Change:** <what you actually did>
       **Result:** IES X.XX → Y.YY, <lines_delta>. <what happened — matched, surprised, or failed?>
       ```
  11. Update $WORK/ideas.md:
       - Cross out the idea in Remaining Ideas
       - If discard: add to Dead Ends with WHY (not just the number)
       - If insight: add to Key Insights
       - If new direction: add to Remaining Ideas
  12. Check stop conditions (see below)
  13. Go to 1
```

## Plateau Detection

If 3 consecutive iterations in Explore fail to improve IES, **switch
categories** before stopping. Invariant categories (from metric.md):
type safety, input validation, contract consistency, scope isolation,
encoding, resource management, state machines, arity, ordering, concurrency.

If you've been working on type safety, switch to input validation or
contract consistency. The Dead Ends table tells you what to avoid; the
Key Insights suggest where to go.

## Stop Conditions

Stop when ANY of these is true:

1. **Ceiling**: 3 consecutive iterations with no improvement AFTER a
   category switch (i.e., 6+ total stalls across 2+ categories)
2. **Clean slate**: 0 unguarded AND 0 convention invariants remain
   AND at least 3 Explore iterations have been attempted
3. **Harness ceiling**: prepare.py can't detect a change you believe is correct
   (note this in ideas.md and stop — don't fight the harness)
4. **Eval error**: prepare.py itself errors (exception, syntax error, import error)

When stopped:
- Record final state in `$WORK/results.tsv`
- Write a one-paragraph summary at the bottom of `$WORK/ideas.md`
- Commit bookkeeping files:
    ```bash
    git -C $REPO add $WORK/results.tsv $WORK/ideas.md $WORK/iteration-log.md $WORK/targets.md
    git -C $REPO commit -m "lean-forge: final bookkeeping"
    ```
- **Do NOT expand the repo's scope.** No new features, modules, or
  capabilities beyond what the invariants require.

## Context Management

- ALWAYS redirect: `> $WORK/run.log 2>&1` or `> $WORK/test.log 2>&1`
- Extract metrics via grep — never cat full logs into context
- On test failure: `tail -30 $WORK/test.log`
- On eval failure: `cat $WORK/run.log` (prepare.py is short)
- Short commit messages: `"lean-forge: add arity check to lambda"`, not paragraphs
- Re-read `$WORK/ideas.md` every iteration (it's small and directs the search)
- Minimize re-reads of prepare.py, targets.md, and source files — only
  re-read when a previous iteration moved or renamed code you need to find

## Computing lines_delta

After each commit, compute the net change:
```bash
git -C $REPO diff --stat HEAD~1 | tail -1
```

Record the full line (e.g., "3 files changed, 15 insertions(+), 2 deletions(-)")
in the `lines_delta` column of results.tsv.

## Timeout

Evaluation: < 5 seconds (prepare.py reads files, no execution).
Tests: repo-dependent. Kill at 5 minutes.

## Tools for Structural Promotion

When promoting validated (2) → structural (3), use the repo's existing
toolchain:

- **Python**: mypy/pyright strict mode for type-level enforcement.
  `NewType`, `@dataclass(frozen=True)`, `Literal` types, `Protocol`.
- **Property-based tests**: Hypothesis for arithmetic and encoding
  invariants (roundtrip, commutativity, bounds). A property test that
  generates random inputs and checks the invariant IS structural
  enforcement — the type system just happens to be the test framework.
- **Rust**: the type system is the primary enforcement mechanism.
  Fixed-size arrays (`[u8; 32]`) over `Vec` for known-size data.
  `Result<T, E>` return types instead of `panic!`/`unwrap`.
  Newtype structs (`struct Difficulty(u8)`) for domain constraints.
  Struct construction to enforce relationships (e.g., a `BlockChain`
  struct that owns the previous hash, making broken linkage impossible).
- **Go**: error return and propagation (`if err != nil { return err }`).
  Defer ordering for resource cleanup (defer close BEFORE operations
  that can fail). Type widening for numeric safety (`uint32` → `uint64`).
  Guard clauses for empty/nil state at function entry. Named types for
  domain semantics.
- **TypeScript**: branded types, discriminated unions, `readonly`
  properties, `as const` assertions.

Do NOT install new type checkers or test frameworks. Use what's already
in the project's toolchain.

## NEVER STOP (until stop conditions)

Do NOT pause to ask the human. Continue until a stop condition is met.
If out of ideas in Explore, try:
- Combine two near-miss changes
- Check if a validated invariant can be made structural (see Tools above)
- Add property-based tests for arithmetic invariants
- Search for cross-module invariants you missed in Phase 0
- Look for invariants that are "invisible when broken" — the system still
  works but produces wrong results
