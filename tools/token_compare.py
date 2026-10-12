"""Run one task headless under several context conditions and compare cost and correctness.

Used in the Day 2 context-efficiency lab. Each trial copies the repository to a
fresh temporary directory, applies a condition, runs `claude -p` with JSON
output, then runs an acceptance command and records whether it passed.

    uv run python tools/token_compare.py --task labs/day2/lab6-context/task.md \
        --accept "uv run pytest tests/validation -q -m 'not advanced' --impl work.lab6:analyze" \
        --condition bare --condition claude_md --condition skill --trials 3 --model sonnet

Conditions
  bare       no CLAUDE.md, no project skills
  claude_md  the repository CLAUDE.md only
  skill      CLAUDE.md plus .claude/skills/waveform-analysis

Output: a table on stdout and a CSV (default results/token_compare.csv).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE = shutil.ignore_patterns(".venv", ".git", "__pycache__", ".pytest_cache", "build", "results")


def prepare(condition: str, dest: Path) -> None:
    shutil.copytree(ROOT, dest, ignore=IGNORE, dirs_exist_ok=True)
    skills = dest / ".claude" / "skills"
    if condition == "bare":
        (dest / "CLAUDE.md").unlink(missing_ok=True)
        shutil.rmtree(skills, ignore_errors=True)
    elif condition == "claude_md":
        shutil.rmtree(skills, ignore_errors=True)
    elif condition != "skill":
        raise ValueError(f"unknown condition {condition}")


DEFAULT_ALLOWED = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(uv run *)", "Bash(ls *)", "Bash(mkdir *)"]


def trial(
    task: str, condition: str, model: str, accept: str, permission_mode: str, timeout: int, allowed: list[str], keep: Path | None = None
) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"tc_{condition}_") as tmp:
        work = Path(tmp)
        prepare(condition, work)
        cmd = [
            "claude",
            "-p",
            task,
            "--output-format",
            "json",
            "--model",
            model,
            "--permission-mode",
            permission_mode,
            "--no-session-persistence",
        ]
        t0 = time.monotonic()
        proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=timeout, check=False)
        wall = time.monotonic() - t0
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            out = {"is_error": True, "result": proc.stdout[-500:] + proc.stderr[-500:]}
        usage = out.get("usage", {})
        check = subprocess.run(accept, cwd=work, shell=True, capture_output=True, text=True, timeout=timeout, check=False)
        if keep is not None:
            dest = keep / f"{condition}_{int(time.time())}"
            shutil.copytree(work, dest, ignore=IGNORE)
            (dest / "_agent_result.json").write_text(json.dumps(out, indent=2))
            (dest / "_acceptance_output.txt").write_text(check.stdout + check.stderr)
        return {
            "condition": condition,
            "model": model,
            "passed": check.returncode == 0,
            "cost_usd": out.get("total_cost_usd"),
            "input_tokens": usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0),
            "output_tokens": usage.get("output_tokens"),
            "turns": out.get("num_turns"),
            "wall_s": round(wall, 1),
            "error": bool(out.get("is_error")),
        }


def summarise(rows: list[dict]) -> None:
    print(f"\n{'condition':10s} {'n':>2s} {'pass':>5s} {'median $':>9s} {'median in-tok':>13s} {'median out-tok':>14s} {'median s':>9s}")
    for cond in dict.fromkeys(r["condition"] for r in rows):
        rs = [r for r in rows if r["condition"] == cond]

        def med(key, rs=rs):
            vals = [r[key] for r in rs if isinstance(r[key], (int, float))]
            return statistics.median(vals) if vals else float("nan")

        print(
            f"{cond:10s} {len(rs):2d} {sum(r['passed'] for r in rs):>2d}/{len(rs):<2d} {med('cost_usd'):9.3f} {med('input_tokens'):13.0f} {med('output_tokens'):14.0f} {med('wall_s'):9.1f}"
        )
    print("\nCost and tokens mean little without the pass column. Small n: treat differences under ~30% as noise.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="markdown file holding the prompt")
    ap.add_argument("--accept", required=True, help="shell command; exit 0 means the work is acceptable")
    ap.add_argument("--condition", action="append", choices=["bare", "claude_md", "skill"], required=True)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--permission-mode", default="auto", help="auto (default) lets the agent run its own tests; dontAsk plus --allow for a locked-down run")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--allow", action="append", help="tool permission rule, repeatable (default: read/edit files, uv run, ls, mkdir)")
    ap.add_argument("--csv", default="results/token_compare.csv")
    ap.add_argument("--keep", type=Path, help="copy each trial's working folder here for inspection")
    args = ap.parse_args()

    task = Path(args.task).read_text()
    rows = []
    for i in range(args.trials):
        for cond in args.condition:
            r = trial(task, cond, args.model, args.accept, args.permission_mode, args.timeout, args.allow or DEFAULT_ALLOWED, args.keep)
            rows.append(r)
            print(
                f"trial {i + 1} {cond:10s} passed={r['passed']} cost=${r['cost_usd']} in={r['input_tokens']} out={r['output_tokens']} {r['wall_s']}s"
            )
    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summarise(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
