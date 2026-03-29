# Phase 0.1b: Lean Formalization

> Center of gravity: **invariant discovery through precision** — writing
> Lean types and theorem signatures forces you to declare what the code
> leaves implicit. The value is in what you discover, not in the proofs.

This phase surfaces invariants that code reading misses. Code reading
finds what IS enforced; formalization finds what SHOULD BE enforced
but isn't.

---

## Setup

Create the Lean project inside the working directory:

```bash
mkdir -p $WORK/lean/Spec
printf ".lake/\nlake-manifest.json\n" >> $WORK/lean/.gitignore
```

Write `$WORK/lean/lakefile.lean`:
```lean
import Lake
open Lake DSL

package «spec» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩
  ]

@[default_target]
lean_lib «Spec» where
  srcDir := "."
```

Write `$WORK/lean/lean-toolchain`:
```
leanprover/lean4:v4.12.0
```

All `.lean` files go in `$WORK/lean/Spec/`.

---

## Scope

You already read the repo in step 0.1. Now identify the **3-5 modules**
where "invisible when broken" is most likely:

- Cross-module data contracts (module A produces, module B consumes)
- State machines / lifecycle transitions
- Type conversions at system boundaries (serialization, encoding, API translation)
- Shared ordering or identity assumptions

Do NOT formalize everything. Focus on boundaries and contracts.

---

## Process

Four discovery operations. Each surfaces a different class of invariant.

### 1. Define domain types

Write Lean structures for the repo's core types. For each type:
- What fields are required to construct it?
- What's the construction invariant (e.g., non-empty list, positive integer)?
- If a field can be `None` in the code but is always needed downstream,
  that's a discovered invariant.

### 2. Define state machines

Write inductive types for entities with lifecycle states. For each:
- What transitions are valid?
- Does the code allow transitions that shouldn't happen?
- Are terminal states truly terminal?

### 3. Write theorem signatures

Write theorem signatures (with `sorry` proofs) for key safety properties.
- What preconditions does the theorem need?
- Each precondition the code doesn't check is a discovered invariant.
- Each `sorry` marks a gap where enforcement is assumed but not proven.

### 4. Run `lake build`

```bash
cd $WORK/lean && lake build 2>&1 | head -30
```

Fix type errors — they reveal structural contradictions. Use `sorry` for
all proofs — the value is in types and signatures, not proofs.

**If `lake build` still has errors after 3 fix attempts, stop and extract
invariants from what you have.** Type errors themselves are discovery
signals — a type mismatch between modules reveals a contract gap. The
build does not need to be clean.

---

## Conventions

- Namespace: `namespace Spec`
- No Mathlib dependency (keep build trivial)
- `autoImplicit` off (forces explicit declarations — every variable must
  be introduced, which surfaces hidden assumptions)
- Section dividers (`-- ════...`) for readability
- Document design choices in comments

---

## Scope Guard

Stop formalizing when:

- You have types for the core domain objects
- You have theorem signatures for the key safety properties
- You've run `lake build` at least once
- You've identified invariants that code reading alone missed

**Cap: 5 `.lean` files, ~200-400 lines each.** This is discovery, not a
comprehensive specification.

---

## Output

Write `$WORK/findings.md`:

```markdown
# Formalization Findings

## Discovered Invariants

### 1. <invariant name>
**Discovery:** <what happened during formalization that surfaced this>
**Current enforcement:** <unguarded | convention | validated | structural>
**Lean evidence:** <which type/theorem revealed it>
**Risk:** <what goes wrong when violated>

### 2. ...

## Lean Spec Summary
- Files: <list of .lean files written>
- `lake build`: <pass | N errors remaining (list them)>
- sorry count: <N> (all proofs are sorry — this is expected)
```

Do NOT commit yet — lean/ and findings.md are Phase 0 artifacts, like
prepare.py. They get committed with the first Phase 1 iteration (the
branch doesn't exist until step 0.6).

---

Return to `analyze.md` for step 0.2.
