"""Setup check, Lab 1 step 1. Run from the repository root:

    uv run python setup/check_setup.py

Prints PASS / WARN / FAIL per item. FAIL items must be fixed before you go on.
"""

from __future__ import annotations

import importlib
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TRUTH = "f51ee682776d38b9caa02557f0d35ddd70df07a6507adc879ee262958d5f4793"
EXPECTED_WAVEFORMS = "0a82171268fd04794867529520fc448eceed20d162472d8ae09bb79b6c020f61"

results: list[tuple[str, str, str]] = []


def record(status: str, item: str, detail: str = "") -> None:
    results.append((status, item, detail))
    print(f"[{status:4s}] {item}" + (f": {detail}" if detail else ""))


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def main() -> int:
    print(f"System: {platform.system()} {platform.release()} ({platform.machine()}), Python {platform.python_version()}\n")

    if sys.version_info >= (3, 12):  # noqa: UP036 (may be run outside uv)
        record("PASS", "Python >= 3.12", platform.python_version())
    else:
        record("FAIL", "Python >= 3.12", f"found {platform.python_version()}; run through `uv run`")

    for mod in ["numpy", "scipy", "matplotlib", "pandas", "pyarrow", "uproot", "pytest", "hypothesis", "wfkit"]:
        try:
            m = importlib.import_module(mod)
            record("PASS", f"import {mod}", getattr(m, "__version__", ""))
        except Exception as e:  # noqa: BLE001
            record("FAIL", f"import {mod}", f"{e}; run `uv sync`")

    try:
        from wfkit.config import PRESETS
        from wfkit.generator import generate
        from wfkit.io import checksums, read_run, write_run

        run_ = generate(PRESETS["sipm_lowlight"], n_events=200, seed=1)
        sums = checksums(run_)
        if sums["truth"] == EXPECTED_TRUTH:
            record("PASS", "generator reproduces reference truth")
        else:
            record(
                "WARN",
                "generator reproduces reference truth",
                "random stream differs from the reference machine; your data and truth are still consistent with each other, but numbers will differ from your neighbours'. Run `uv sync` and tell the organiser",
            )
        if sums["waveforms"] == EXPECTED_WAVEFORMS:
            record("PASS", "waveforms bit-identical to reference")
        else:
            record("WARN", "waveforms bit-identical to reference", "last-bit float differences on this platform; results unaffected")
        with tempfile.TemporaryDirectory() as d:
            paths = write_run(run_, Path(d) / "t", formats=("parquet", "root"))
            ok = all((read_run(paths[f]).waveforms == run_.waveforms).all() for f in ("parquet", "root"))
            record("PASS" if ok else "FAIL", "Parquet and ROOT round trip")
    except Exception as e:  # noqa: BLE001
        record("FAIL", "wfkit generator", str(e))

    data = ROOT / "data"
    if all((data / f"{n}.parquet").exists() for n in ("sipm_lowlight", "sipm_highlight", "sipm_dark", "pmt_spe", "coincidence")):
        record("PASS", "workshop datasets present", str(data))
    else:
        record("WARN", "workshop datasets present", "run `uv run wfkit generate --all` (about 30 s)")

    for tool, why in [("git", "version control"), ("claude", "Claude Code")]:
        path = shutil.which(tool)
        if not path:
            record("FAIL", f"{tool} on PATH", f"needed for {why}; see setup/SETUP.md")
            continue
        code, out = run([tool, "--version"])
        record("PASS" if code == 0 else "FAIL", f"{tool} --version", out.splitlines()[0] if out else "")

    if shutil.which("claude"):
        code, out = run(["claude", "-p", "Reply with exactly: ready", "--model", "haiku", "--output-format", "text"], timeout=120)
        if code == 0 and "ready" in out.lower():
            record("PASS", "Claude Code signed in and answering")
        else:
            record("FAIL", "Claude Code signed in and answering", "run `claude` once and sign in with your Claude account")

    cxx = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    cmake = shutil.which("cmake")
    if cmake and cxx:
        record("PASS", "C++ toolchain (optional, for challenges C3/C7)", cxx)
    else:
        missing = " and ".join(name for name, found in (("cmake", cmake), ("a C++ compiler", cxx)) if not found)
        record("WARN", "C++ toolchain (optional, for challenges C3/C7)", f"{missing} not found; only needed for C3/C7")

    fails = sum(1 for s, *_ in results if s == "FAIL")
    warns = sum(1 for s, *_ in results if s == "WARN")
    print(f"\n{len(results) - fails - warns} passed, {warns} warnings, {fails} failures.")
    if fails:
        print("Fix the failures above, then run this again. Bring the output to the help desk if stuck.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
