# Invariant Enforcement Score (IES)

> Center of gravity: **the scoring definition** — how to classify invariants
> and write check functions. Reference this when writing prepare.py, not
> during the optimization loop.

## The metric

For a system with N critical invariants, classify each by enforcement level:

| Level | Score | Meaning | How to detect |
|---|---|---|---|
| **Structural** | 3 | Impossible to violate. Types enforce at construction. | No preconditions needed to guarantee correctness. Types, validators, or constructors prevent invalid states. |
| **Validated** | 2 | Caught before damage. Runtime check at the boundary. | Explicit check (if/raise, assert, try/except) before the dangerous operation. Clear error message. |
| **Convention** | 1 | Relies on discipline. Documented but not enforced. | Comment says "must be X" but code doesn't check. Tests exercise the happy path only. |
| **Unguarded** | 0 | No enforcement. Fails silently or crashes. | Raw exception (KeyError, IndexError, TypeError) or silent wrong result on bad input. |

**IES = Σ(scores) / (3 × N)**

Range [0, 1]. Higher is more robust.

## How to identify invariants

An invariant is a property that MUST be true for the system to produce correct
results. When violated, the system either crashes, produces wrong output, or
silently corrupts downstream data.

### Common categories

Scan the codebase for these patterns. Not every category applies to every repo.

**State machines** — Does the system have entities with lifecycle states?
- Invariant: transitions follow a valid order (no skipping, no cycles)
- Structural: enum with transition function. Validated: status checks before transitions.

**Type safety** — Are operations applied to values of the right type?
- Invariant: arithmetic only on numbers, calls only on callables, indexing only on sequences
- Structural: type annotations enforced at boundaries. Validated: isinstance checks.

**Scope / isolation** — Do bindings, connections, or state leak between contexts?
- Invariant: one context's state doesn't affect another
- Structural: immutable data or environment chains. Validated: cleanup in finally/context manager.

**Input validation** — Are inputs checked at system boundaries?
- Invariant: malformed input produces a clear error, not a crash or wrong result
- Structural: parsed types (Pydantic, dataclass with validators). Validated: explicit checks.

**Encoding / serialization** — Do two representations of the same data agree?
- Invariant: serialize then deserialize = identity (roundtrip)
- Structural: one function wraps the other. Validated: roundtrip test.

**Concurrency** — Can concurrent access corrupt shared state?
- Invariant: critical sections are mutually exclusive
- Structural: immutable data. Validated: locks, atomic operations.

**Resource management** — Are connections, files, handles cleaned up?
- Invariant: every acquire has a matching release, even on error
- Structural: context manager (with statement). Validated: try/finally.

**Arity / cardinality** — Are collections the expected size?
- Invariant: function called with right number of args, list has expected length
- Structural: typed tuples, dataclasses. Validated: len() checks before access.

**Ordering** — Does the order of elements matter for correctness?
- Invariant: elements are in canonical order (sorted, deduplicated)
- Structural: sorted container type. Validated: sort + dedup at construction.

**Contract consistency** — Do two modules agree on a shared interface?
- Invariant: producer's output matches consumer's expected input
- Structural: shared type definition imported by both. Validated: schema check.
- **These are the highest-value invariants.** Cross-module contracts are often
  convention (1) or unguarded (0) because each module was written independently.
  Violations are invisible — the system still serves, still computes, but
  produces wrong results. Trace the import graph: where does module A pass
  data to module B? What does B assume about the format?

### What makes a GOOD invariant for IES

- **Invisible when broken**: the system still serves, still renders, still
  computes — but produces wrong results. These are the invariants that code
  reading misses because nothing visibly fails.
- **Specific**: "undefined symbol lookup crashes with KeyError" not "error handling is bad"
- **Checkable**: you can write a prepare.py function that detects the enforcement level
- **Improvable**: there's a concrete code change that raises the score

### What to SKIP

- Style preferences (naming, formatting, docstrings)
- Performance characteristics (unless they cause correctness issues)
- Features the code doesn't have (missing functionality ≠ broken invariant)
- Test coverage as a standalone metric (it's one invariant, not the whole score)

## Writing prepare.py

Template:

```python
"""IES evaluation harness for <repo name>.

Read-only. Examines source code and computes IES.

Usage:
    python3 prepare.py
"""
from pathlib import Path
import ast  # for structural detection; see check function guidelines below
import re

REPO = Path("<absolute path to repo>")
SRC = REPO / "<path to main source>"

def check_01_<invariant_name>() -> tuple[int, str]:
    """<What the invariant is>."""
    content = SRC.read_text()
    # Check for structural enforcement (score 3)
    if <pattern that indicates type-level enforcement>:
        return 3, "<explanation>"
    # Check for validated enforcement (score 2)
    if <pattern that indicates runtime check>:
        return 2, "<explanation>"
    # Check for convention (score 1)
    if <pattern that indicates documentation but no check>:
        return 1, "<explanation>"
    # Unguarded (score 0)
    return 0, "<explanation of what goes wrong>"

# ... one check function per invariant ...

INVARIANTS = [
    ("invariant_name", check_01_invariant_name),
    # ...
]

LEVEL_NAMES = {3: "structural", 2: "validated", 1: "convention", 0: "unguarded"}

def main() -> None:
    results = []
    for name, check_fn in INVARIANTS:
        score, explanation = check_fn()
        results.append((name, score, explanation))

    print("=" * 78)
    print(f"{'Invariant':<28} {'Score':<6} {'Level':<12} Explanation")
    print("-" * 78)
    for name, score, explanation in results:
        level = LEVEL_NAMES[score]
        print(f"{name:<28} {score:<6} {level:<12} {explanation}")
    print("=" * 78)

    scores = [r[1] for r in results]
    n = len(scores)
    total = sum(scores)
    ies = total / (3 * n) if n > 0 else 0

    print()
    print(f"ies_score: {ies:.4f}")
    print(f"ies_numerator: {total}")
    print(f"ies_denominator: {3 * n}")
    print(f"invariant_count: {n}")
    print(f"structural_count: {sum(1 for s in scores if s == 3)}")
    print(f"validated_count: {sum(1 for s in scores if s == 2)}")
    print(f"convention_count: {sum(1 for s in scores if s == 1)}")
    print(f"unguarded_count: {sum(1 for s in scores if s == 0)}")

if __name__ == "__main__":
    main()
```

### Check function guidelines

- **Extract scope first, then detect.** Every check should start by
  extracting the relevant function or class body using `re.DOTALL`.
  Adapt the pattern to the target language:
  ```python
  # Python
  match = re.search(r'def\s+my_func\(.*?\).*?(?=\ndef\s|\nclass\s|\Z)',
                    content, re.DOTALL)
  # Go
  match = re.search(r'func\s+(?:\(.*?\)\s+)?MyFunc\(.*?\)\s*(?:\(.*?\)\s*)?\{.*?\n\}',
                    content, re.DOTALL)
  # Rust
  match = re.search(r'(?:pub\s+)?fn\s+my_func\(.*?\).*?\{.*?\n\}',
                    content, re.DOTALL)
  ```
  Then search within `body`. This handles multiline formatting naturally.
- **Check for the EFFECT, not the exact code shape.** A runtime check
  can be: `isinstance()`, `raise TypeError`, `assert`, a bound check,
  `if x not in`, or a validator decorator. Use alternation (`|`) in
  regex to catch variants. If the invariant is "bad input raises an
  error," detect any of the ways that could happen.
- **Use `re.DOTALL` for any pattern that might span lines.** Raise
  statements, compound conditions, guard clauses, and return type
  annotations routinely span multiple lines in real code.
- **Mental robustness test.** For each check, ask: if a developer
  implements this invariant with different formatting (multiline raise,
  guard on a separate line, return type on next line), does the regex
  still match? If not, make it more permissive before freezing.
- For Python repos, `ast.parse()` provides more reliable structural
  detection than regex. Use it when formatting variations would make
  regex fragile (e.g., detecting whether a function raises a specific
  exception type).
- **Cross-language detection patterns.** prepare.py is always Python,
  but the target repo may be any language. Adjust regex patterns:
  - **Go**: structural = named types, error returns (`func.*error`);
    validated = `if err != nil`, bounds checks; unguarded = unchecked
    error (`_ = someFunc()`), missing nil guard before dereference.
  - **Rust**: structural = `Result<T, E>` return, newtype structs,
    fixed-size arrays (`[u8; N]`); validated = `assert!`, `if let`,
    match arms; unguarded = `.unwrap()`, `.expect()`, unchecked indexing.
  - **TypeScript/JavaScript**: structural = branded types, discriminated
    unions; validated = `typeof`/`instanceof` checks, `if (!x) throw`;
    unguarded = unchecked property access, `as` type assertions.
- Use `re.search()` for pattern detection, not exact string matching.
  Code changes may vary in whitespace, naming, or placement.
- Check multiple file locations (the agent might move code between modules).
- Score the WEAKEST code path. If 3 of 4 constructors validate but the
  4th doesn't, the invariant is unguarded (0). The invariant is only as
  strong as its weakest enforcement. Exception: if a single path has both
  type-level enforcement AND a redundant runtime check, score the path as
  structural (3) — the type subsumes the check.
- Each check must produce a non-empty explanation string.
- Avoid false positives: `isinstance(x, int)` in a type dispatch is NOT
  the same as `isinstance(x, int)` as an argument validator.
