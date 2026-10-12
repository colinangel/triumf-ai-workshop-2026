"""Lab 2 part B: the same unit conversion, done by the model in its head and by code.

Asks Claude, with every tool switched off, to convert a pulse integral from ADC
counts x samples to pC and electrons. It runs the question several times at low and
at high reasoning effort, prints each answer as it comes back with a right or WRONG
verdict, then a tally.

    uv run python labs/day1/lab2-trust/arith_trial.py                 # Sonnet, 10 runs each at low and high
    uv run python labs/day1/lab2-trust/arith_trial.py --n 5 --model haiku
    uv run python labs/day1/lab2-trust/arith_trial.py --show-working   # also print the full working of each wrong answer
    uv run python labs/day1/lab2-trust/arith_trial.py --json work/lab2b.json   # keep the raw results

Run it from a terminal, or ask Claude Code to run it and explain the table.
Each run is one `claude -p` call with no tools: on Sonnet, about $0.01 at list price.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

ADC_SAMPLES = 1853
DT_NS, MV_PER_ADC, IMPEDANCE_OHM, PREAMP_GAIN = 4.0, 0.1220703125, 50.0, 30.0  # the sipm_lowlight run
ELEMENTARY_CHARGE_C = 1.602176634e-19

# mV x ns / ohm = pC
TRUE_PC = ADC_SAMPLES * MV_PER_ADC * DT_NS / IMPEDANCE_OHM / PREAMP_GAIN
TRUE_ELECTRONS = TRUE_PC * 1e-12 / ELEMENTARY_CHARGE_C
TOLERANCE = 0.01  # 1 %

PROMPT = f"""Without using any tools, work this out yourself.

A SiPM waveform was recorded with this digitiser and front end:
{{
 "dt_ns": {DT_NS},
 "mv_per_adc": {MV_PER_ADC},
 "impedance_ohm": {IMPEDANCE_OHM},
 "preamp_gain": {PREAMP_GAIN},
 "polarity": "negative",
 "adc_bits": 14,
 "full_scale": "2 V peak to peak"
}}

After baseline subtraction and flipping the sign of the negative pulse, the sum of the samples over the integration gate is {ADC_SAMPLES} ADC counts (summed over the gate's samples, so the unit is ADC count x sample).

What is the charge at the sensor in pC, and how many electrons is that?
End with one line exactly: ANSWER: <charge> pC, <electrons> electrons"""

_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_NUMBER = r"([-+]?\d[\d,]*(?:\.\d+)?(?:\s*(?:[eE]|[x×]\s*10\^?)\s*[-+]?\d+)?)"


def _to_float(text: str) -> float:
    t = text.translate(_SUPERSCRIPT).replace(",", "").replace(" ", "")
    t = re.sub(r"[x×]10\^?", "e", t)
    return float(t)


@dataclass
class Score:
    parsed: bool
    correct: bool
    pc: float | None = None
    electrons: float | None = None
    factor: float | None = None  # answer / true charge


def score(reply: str) -> Score:
    lines = re.findall(r"ANSWER:\s*(.+)", reply)
    if not lines:
        return Score(parsed=False, correct=False)
    line = lines[-1].translate(_SUPERSCRIPT)
    pc = re.search(_NUMBER + r"\s*pC", line)
    el = re.search(_NUMBER + r"\s*electrons", line)
    if not (pc and el):
        return Score(parsed=False, correct=False)
    pcv, elv = _to_float(pc.group(1)), _to_float(el.group(1))
    factor = pcv / TRUE_PC
    ok = abs(factor - 1) < TOLERANCE and abs(elv / TRUE_ELECTRONS - 1) < TOLERANCE
    return Score(parsed=True, correct=ok, pc=pcv, electrons=elv, factor=factor)


def _clean_env() -> dict[str, str]:
    # Inside a Claude Code session these would leak into the child run.
    return {k: v for k, v in os.environ.items() if k not in {"CLAUDECODE", "CLAUDE_EFFORT"}}


def run_once(model: str, effort: str, workdir: str) -> dict:
    cmd = ["claude", "-p", PROMPT, "--model", model, "--effort", effort, "--tools", "",
           "--setting-sources", "user", "--output-format", "json"]
    t0 = time.monotonic()
    try:
        out = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=600, env=_clean_env(), check=False)
        data = json.loads(out.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"effort": effort, "error": f"{type(exc).__name__}: {(locals().get('out') and out.stderr or '')[:200]}"}
    if data.get("is_error"):
        return {"effort": effort, "error": str(data.get("result", ""))[:200]}
    s = score(data.get("result", ""))
    answer = (re.findall(r"ANSWER:\s*(.+)", data.get("result", "")) or [""])[-1]
    return {"effort": effort, "seconds": round(time.monotonic() - t0, 1), "cost_usd": data.get("total_cost_usd") or 0.0,
            "tool_turns": data.get("num_turns", 1) - 1, "answer": answer.strip(), "reply": data.get("result", ""), **asdict(s)}


def live_line(n: int, r: dict) -> str:
    """One line per finished run, printed as it arrives."""
    head = f"  #{n:<3} effort {r['effort']:<5}"
    if "error" in r:
        return f"{head} run failed: {r['error'][:70]}"
    if not r.get("parsed"):
        return f"{head} no ANSWER line ({r['seconds']:.0f} s)"
    verdict = "right" if r["correct"] else f"WRONG  x{r['factor']:.3g} of the true charge"
    return f"{head} {r['answer'][:46]:<46} {verdict}  ({r['seconds']:.0f} s)"


def _code_answer() -> tuple[float, float, float]:
    t0 = time.perf_counter()
    pc = ADC_SAMPLES * MV_PER_ADC * DT_NS / IMPEDANCE_OHM / PREAMP_GAIN
    el = pc * 1e-12 / ELEMENTARY_CHARGE_C
    return pc, el, time.perf_counter() - t0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--n", type=int, default=10, help="runs per effort setting (default 10)")
    ap.add_argument("--effort", nargs="+", default=["low", "high"], help="effort settings to compare (default: low high)")
    ap.add_argument("--jobs", type=int, default=5, help="runs in parallel (default 5)")
    ap.add_argument("--show-working", action="store_true", help="after the tally, print the full reply of each wrong answer")
    ap.add_argument("--json", type=Path, help="also write every result to this file")
    a = ap.parse_args(argv)
    if not shutil.which("claude"):
        print("claude not found on PATH: install Claude Code first (setup/SETUP.md)", file=sys.stderr)
        return 2

    pc, el, secs = _code_answer()
    print(f"Lab 2 part B: unit chain, {a.model}, tools off, {a.n} runs per setting\n")
    print(f"code (Python): {pc:.5f} pC, {el:.4e} electrons, in {secs * 1e6:.0f} microseconds\n")

    print("answers as they come back (true value 0.6032 pC, 3.765e6 electrons):")
    with tempfile.TemporaryDirectory() as work, ThreadPoolExecutor(max_workers=a.jobs) as pool:
        jobs = [pool.submit(run_once, a.model, e, work) for e in a.effort for _ in range(a.n)]
        results = []
        for i, j in enumerate(as_completed(jobs), 1):
            r = j.result()
            results.append(r)
            print(live_line(i, r), flush=True)
    print()

    print(f"{'setting':<14}{'right':>6}{'wrong':>7}{'errors':>8}{'median s':>10}{'cost/run':>10}")
    for e in a.effort:
        rs = [r for r in results if r["effort"] == e]
        ok = [r for r in rs if "error" not in r]
        right = sum(r["correct"] for r in ok)
        med = sorted(r["seconds"] for r in ok)[len(ok) // 2] if ok else float("nan")
        cost = sum(r["cost_usd"] for r in ok) / len(ok) if ok else float("nan")
        print(f"{'effort ' + e:<14}{right:>6}{len(ok) - right:>7}{len(rs) - len(ok):>8}{med:>10.0f}{'$' + format(cost, '.4f'):>10}")

    wrong = [r for r in results if "error" not in r and not r["correct"]]
    if a.show_working:
        for k, r in enumerate(wrong, 1):
            print(f"\n--- wrong answer {k} of {len(wrong)}, effort {r['effort']} ---\n{r['reply'].strip()}")
    elif wrong:
        print("\nadd --show-working to read the full working of the wrong answers")
    errors = [r for r in results if "error" in r]
    if errors:
        print(f"\n{len(errors)} run(s) failed to complete, for example: {errors[0]['error']}")
    if any(r.get("tool_turns") for r in results):
        print("\nnote: some runs used a tool; those answers are not the model's own arithmetic")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({"model": a.model, "true_pc": TRUE_PC, "results": results}, indent=1))
        print(f"\nraw results: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
