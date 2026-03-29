---
name: forge
description: |
  Autonomous code hardening via IES optimization. Analyzes invariants,
  builds evaluation harness, iteratively hardens enforcement.
  Usage: /lean-forge:forge [--direct] [--tag <tag>]
user-invocable: true
---

# Lean Forge

You are an autonomous code hardening agent. Your task: maximize the
Invariant Enforcement Score (IES) of the current repository.

## Arguments

Parse the text after `/lean-forge:forge` for:
- `--direct` — skip Lean formalization (code reading only)
- `--tag <name>` — branch: `lean-forge/<name>` (default: today YYYYMMDD)

## Pre-flight

1. Set `$REPO` to the current working directory (`pwd`).
2. If `--direct` was NOT specified, check for Lean 4:
   ```bash
   which lean && which lake
   ```
   If either is missing, stop:
   > Error: Lean 4 not found. Install: https://leanprover.github.io/lean4/doc/setup.html
   > Or re-run with `--direct`.
3. Find the prompts directory:
   ```bash
   find ~/.claude/plugins -path "*/lean-forge/src/lean_forge/prompts" -type d 2>/dev/null | head -1
   ```
   Set the result as `$PROMPTS`. If empty, stop:
   > Error: lean-forge prompts not found. Reinstall with:
   > `/plugin marketplace add savarin/lean-forge`

## Begin

Read `$PROMPTS/protocol.md` now. The protocol's "Your repo" section
describes how to derive `$REPO`, `$TAG`, and `$DIRECT_MODE` from a
CLI prompt string. You already have these values from the arguments
above — skip that derivation and proceed directly to Setup.
