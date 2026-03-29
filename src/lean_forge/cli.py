"""lean-forge CLI: autonomous code hardening via IES optimization."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="Run autonomous IES optimization on a repository",
    )
    parser.add_argument("repo", help="Path to target repository")
    parser.add_argument(
        "--model", default="opus", help="Claude model (default: opus)"
    )
    parser.add_argument(
        "--effort", default="max", help="Effort level (default: max)"
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Branch tag: lean-forge/<tag> (default: YYYYMMDD)",
    )
    parser.add_argument(
        "--skip-permissions",
        action="store_true",
        help="Skip permission prompts for autonomous operation",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Skip Lean formalization, use code reading only",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=200,
        help="Maximum claude turns (default: 200)",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Error: {repo} is not a directory", file=sys.stderr)
        sys.exit(1)

    if not args.direct:
        if not shutil.which("lean") or not shutil.which("lake"):
            print(
                "Error: Lean 4 not found. Install from "
                "https://leanprover.github.io/lean4/doc/setup.html\n"
                "Or use --direct to skip formalization.",
                file=sys.stderr,
            )
            sys.exit(1)

    tag = args.tag or datetime.now().strftime("%Y%m%d")

    protocol_md = PROMPTS_DIR / "protocol.md"
    if not protocol_md.exists():
        print(f"Error: prompts not found at {protocol_md}", file=sys.stderr)
        sys.exit(1)

    cmd = ["claude"]
    cmd.extend(["--model", args.model])
    cmd.extend(["--effort", args.effort])
    cmd.extend(["--max-turns", str(args.max_turns)])
    if args.skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    prompt = f"Read {protocol_md} for {repo} tag {tag}"
    if args.direct:
        prompt += " direct"
    cmd.append(prompt)

    os.execvp("claude", cmd)
