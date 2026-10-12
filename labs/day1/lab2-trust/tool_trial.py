"""Lab 2 part D: the same kind of numbers, read from a tool instead of worked out.

Asks Claude to run `wfkit info` on the sipm_lowlight run and report the sample period and the
preamplifier gain. It runs the question as many times as part C's calculation trial, at the same
low and high reasoning effort, and prints each answer as it comes back, marked right or WRONG
against the run's metadata, then a tally and how many different wordings the answers used.

    uv run python labs/day1/lab2-trust/tool_trial.py
    uv run python labs/day1/lab2-trust/tool_trial.py --model opus
    uv run python labs/day1/lab2-trust/tool_trial.py --show-replies   # print every full reply

Claude may run only that one command: every other tool and command is refused.
Each run is one `claude -p` call: on Sonnet, a few cents at list price.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = "data/sipm_lowlight.parquet"
COMMAND = f"uv run wfkit info {DATA}"
TRUE_DT_NS, TRUE_GAIN = 4.0, 30.0  # from the run metadata; checked against the file at start-up

PROMPT = f"""Run `{COMMAND}` and tell me the sample period and the preamplifier gain of this run.
End with one line exactly: ANSWER: <sample period> ns, gain <preamplifier gain>"""

_NUM = r"([-+]?\d+(?:\.\d+)?)"


@dataclass
class Score:
    parsed: bool
    correct: bool
    dt_ns: float | None = None
    gain: float | None = None


def score(reply: str) -> Score:
    lines = re.findall(r"ANSWER:\s*(.+)", reply)
    m = re.search(_NUM + r"\s*ns.*?gain\D*" + _NUM, lines[-1]) if lines else None
    if not m:
        return Score(parsed=False, correct=False)
    dt, gain = float(m.group(1)), float(m.group(2))
    return Score(parsed=True, correct=dt == TRUE_DT_NS and gain == TRUE_GAIN, dt_ns=dt, gain=gain)


def distinct(replies: list[str]) -> int:
    return len({" ".join(r.split()) for r in replies})


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in {"CLAUDECODE", "CLAUDE_EFFORT"}}


def run_once(model: str, effort: str) -> dict:
    cmd = ["claude", "-p", PROMPT, "--model", model, "--effort", effort, "--tools", "Bash",
           "--allowedTools", f"Bash({COMMAND})", "--permission-mode", "default",
           "--setting-sources", "user", "--output-format", "json"]
    t0 = time.monotonic()
    try:
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600, env=_clean_env(), check=False)
        data = json.loads(out.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"effort": effort, "error": type(exc).__name__}
    if data.get("is_error"):
        return {"effort": effort, "error": str(data.get("result", ""))[:200]}
    reply = data.get("result", "")
    answer = (re.findall(r"ANSWER:\s*(.+)", reply) or [""])[-1].strip()
    return {"effort": effort, "seconds": round(time.monotonic() - t0, 1), "cost_usd": data.get("total_cost_usd") or 0.0,
            "tool_calls": max(0, data.get("num_turns", 1) - 1), "answer": answer, "reply": reply, **asdict(score(reply))}


def live_line(n: int, r: dict) -> str:
    head = f"  #{n:<3} effort {r['effort']:<5}"
    if "error" in r:
        return f"{head} run failed: {r['error'][:70]}"
    calls = "no tool call" if r["tool_calls"] == 0 else f"{r['tool_calls']} tool call" + ("s" if r["tool_calls"] > 1 else "")
    if not r.get("parsed"):
        return f"{head} no ANSWER line, {calls} ({r['seconds']:.0f} s)"
    verdict = "right" if r["correct"] else "WRONG"
    return f"{head} {r['answer'][:30]:<30} {verdict:<6} {calls} ({r['seconds']:.0f} s)"


def _check_truth() -> None:
    out = subprocess.run(COMMAND.split(), cwd=ROOT, capture_output=True, text=True, check=False)
    if out.returncode != 0:
        sys.exit(f"`{COMMAND}` failed; generate the data first: uv run wfkit generate --all\n{out.stderr[-300:]}")
    meta = json.loads(out.stdout)
    if (meta["dt_ns"], meta["preamp_gain"]) != (TRUE_DT_NS, TRUE_GAIN):
        sys.exit(f"metadata changed: dt_ns {meta['dt_ns']}, preamp_gain {meta['preamp_gain']}; update TRUE_DT_NS and TRUE_GAIN")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--n", type=int, default=10, help="runs per effort setting (default 10, as in part C)")
    ap.add_argument("--effort", nargs="+", default=["low", "high"], help="effort settings (default: low high, as in part C)")
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--show-replies", action="store_true", help="after the tally, print every full reply")
    ap.add_argument("--json", type=Path, help="also write every result to this file")
    a = ap.parse_args(argv)
    if not shutil.which("claude"):
        print("claude not found on PATH: install Claude Code first (setup/SETUP.md)", file=sys.stderr)
        return 2
    _check_truth()

    print(f"Lab 2 part D: numbers from a tool, {a.model}, {a.n} runs per setting\n")
    print(f"the tool itself (`{COMMAND}`): {TRUE_DT_NS} ns, gain {TRUE_GAIN:g}\n")
    print("answers as they come back:")
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        jobs = [pool.submit(run_once, a.model, e) for e in a.effort for _ in range(a.n)]
        results = []
        for i, j in enumerate(as_completed(jobs), 1):
            results.append(j.result())
            print(live_line(i, results[-1]), flush=True)
    print()

    print(f"{'setting':<14}{'right':>6}{'wrong':>7}{'errors':>8}{'wordings':>10}{'median s':>10}{'cost/run':>10}")
    for e in a.effort:
        rs = [r for r in results if r["effort"] == e]
        ok = [r for r in rs if "error" not in r]
        right = sum(r["correct"] for r in ok)
        med = sorted(r["seconds"] for r in ok)[len(ok) // 2] if ok else float("nan")
        cost = sum(r["cost_usd"] for r in ok) / len(ok) if ok else float("nan")
        words = f"{distinct([r['reply'] for r in ok])}/{len(ok)}"
        print(f"{'effort ' + e:<14}{right:>6}{len(ok) - right:>7}{len(rs) - len(ok):>8}{words:>10}{med:>10.0f}{'$' + format(cost, '.4f'):>10}")
    print("\n'wordings' counts how many of the replies differ in their text: the numbers come from the tool, the words do not.")
    if any("error" not in r and r["tool_calls"] == 0 for r in results):
        print("note: some answers did not call the tool; those numbers are the model's own")
    if a.show_replies:
        for k, r in enumerate([r for r in results if "error" not in r], 1):
            print(f"\n--- reply {k}, effort {r['effort']} ---\n{r['reply'].strip()}")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({"model": a.model, "results": results}, indent=1))
        print(f"\nraw results: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
