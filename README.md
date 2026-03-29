# lean-forge

Autonomous code hardening via IES (Invariant Enforcement Score) optimization.

Wraps Claude to analyze a repository's invariants, build an evaluation harness,
and iteratively improve enforcement — from unguarded (0) through convention (1)
and validated (2) to structural (3).

## Install

### As a Claude Code plugin (recommended)

```
/plugin marketplace add savarin/lean-forge
/plugin install lean-forge@lean-forge
```

Then invoke in any repo:

```
/lean-forge:forge                     # default: Lean formalization + optimization
/lean-forge:forge --direct            # skip formalization, code reading only
/lean-forge:forge --tag my-hardening  # custom branch name
```

### As a standalone CLI

```bash
uv tool install .
```

```bash
forge <repo>                          # default: Lean formalization + optimization (requires Lean 4)
forge <repo> --direct                 # skip formalization, code reading only
forge <repo> --model sonnet           # use a different model
forge <repo> --tag my-hardening       # branch: lean-forge/my-hardening
forge <repo> --skip-permissions       # autonomous operation (no permission prompts)
forge <repo> --max-turns 300          # increase turn limit (default: 200)
```

## What it does

1. **Analyzes** the repo — identifies 5-15 critical invariants
2. **Builds** `prepare.py` — an evaluation harness that scores each invariant
3. **Executes** known improvements — pre-planned targets, sequentially
4. **Explores** further improvements — AUTORESEARCH discovery loop
5. **Stops** when ceiling is reached or all invariants are covered

Output lives in `<repo>/.lean-forge/` on a `lean-forge/<tag>` branch.

## Example

[`ledger.py`](https://github.com/savarin/ledger) — a 13-line double-entry ledger with five silent failure modes:

```python
class Ledger:
    def __init__(self):
        self.accounts = {}

    def create_account(self, account_id, opening_balance):
        self.accounts[account_id] = opening_balance

    def transfer(self, from_id, to_id, amount):
        self.accounts[from_id] -= amount
        self.accounts[to_id] += amount

    def balance(self, account_id):
        return self.accounts[account_id]
```

`forge ledger-repo` discovers five invariants the code assumes but doesn't
enforce — balances must be non-negative, transfer amounts must be positive,
accounts can't be duplicated, transfers require both accounts to exist, and
self-transfers are meaningless. Lean formalization surfaces these by forcing
explicit type declarations (e.g., defining `Balance` with `val : Nat` makes
negativity structurally impossible, revealing that the Python code allows it
silently).

After hardening:

```python
from typing import NewType

AccountId = NewType("AccountId", str)


class PositiveAmount:
    def __init__(self, value: int | float):
        if value <= 0:
            raise ValueError("amount must be positive")
        self.value = value


class TransferRequest:
    def __init__(self, from_id: AccountId, to_id: AccountId, amount: int | float):
        if from_id == to_id:
            raise ValueError("cannot transfer to same account")
        self.from_id = from_id
        self.to_id = to_id
        self.amount = amount


class Ledger:
    def __init__(self):
        self.accounts = {}

    def create_account(self, account_id: str, opening_balance: int | float) -> None:
        if account_id in self.accounts:
            raise ValueError(f"account '{account_id}' already exists")
        self.accounts[account_id] = opening_balance

    def transfer(self, from_id: AccountId, to_id: AccountId, amount: int | float) -> None:
        if from_id == to_id:
            raise ValueError("cannot transfer to same account")
        if from_id not in self.accounts:
            raise KeyError(f"source account '{from_id}' does not exist")
        if to_id not in self.accounts:
            raise KeyError(f"destination account '{to_id}' does not exist")
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.accounts = {
            **self.accounts,
            from_id: self.accounts[from_id] - amount,
            to_id: self.accounts[to_id] + amount,
        }

    def balance(self, account_id: AccountId) -> int | float:
        if account_id not in self.accounts:
            raise KeyError(f"account '{account_id}' does not exist")
        return self.accounts[account_id]
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (`claude` on PATH)
- Python >= 3.10
- [Lean 4](https://leanprover.github.io/lean4/doc/setup.html) (`lean` and `lake` on PATH) — required for default mode, not needed with `--direct`
