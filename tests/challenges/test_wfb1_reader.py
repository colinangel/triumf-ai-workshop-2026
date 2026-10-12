"""Acceptance tests for the C++ WFB1 reader challenge (C3).

Builds legacy/cpp with CMake unless WFB1_READER points at another binary, runs
it on a generated file, and checks every row against an independent Python
reading of the same events. Skips if no C++ toolchain is available.

Run:  uv run pytest tests/challenges/test_wfb1_reader.py -v
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wfkit.config import PRESETS
from wfkit.generator import generate
from wfkit.io import write_wfb1

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def reader(tmp_path_factory) -> Path:
    if os.environ.get("WFB1_READER"):
        return Path(os.environ["WFB1_READER"])
    if not (shutil.which("cmake") and (shutil.which("c++") or shutil.which("g++") or shutil.which("clang++"))):
        pytest.skip("no CMake / C++ compiler on this machine")
    build = tmp_path_factory.mktemp("build")
    subprocess.run(
        ["cmake", "-S", str(ROOT / "legacy" / "cpp"), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"], check=True, capture_output=True
    )
    subprocess.run(["cmake", "--build", str(build)], check=True, capture_output=True)
    exe = next(p for p in build.rglob("wfb1_reader*") if p.is_file() and os.access(p, os.X_OK))
    return exe


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    cfg = PRESETS["coincidence"]  # two channels, so channel handling is exercised too
    run = generate(cfg, n_events=500, seed=77)
    path = write_wfb1(run, tmp_path_factory.mktemp("raw") / "run.wfb1")
    wf = run.waveforms.astype(np.float64)
    base = wf[:, :, 0:100].mean(axis=2)
    charge = (base[:, :, None] - wf[:, :, 120:200]).sum(axis=2)
    rows = []
    sat = run.truth.pivot(index="event", columns="channel", values="saturated").to_numpy()
    for e in range(wf.shape[1]):
        flags = int(sum(1 << c for c in range(wf.shape[0]) if sat[e, c]))
        for c in range(wf.shape[0]):
            rows.append((e, c, flags, base[c, e], charge[c, e]))
    expected = pd.DataFrame(rows, columns=["event", "channel", "flags", "baseline_adc", "charge_adc_samples"])
    return path, expected


def _run(reader: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([str(reader), *map(str, args)], capture_output=True, text=True, timeout=60, check=False)


def test_reads_every_event_with_correct_ids(reader, sample):
    path, expected = sample
    out = _run(reader, path)
    assert out.returncode == 0, out.stderr
    got = pd.read_csv(io.StringIO(out.stdout))
    assert len(got) == len(expected), f"{len(got)} rows, expected {len(expected)}"
    assert got["event"].tolist() == expected["event"].tolist(), "event ids are not 0,0,1,1,2,2,..."


def test_baseline_and_charge_match_reference(reader, sample):
    path, expected = sample
    got = pd.read_csv(io.StringIO(_run(reader, path).stdout))
    np.testing.assert_allclose(
        got["baseline_adc"], expected["baseline_adc"], rtol=0, atol=1e-6, err_msg="baseline must be the floating-point mean"
    )
    np.testing.assert_allclose(got["charge_adc_samples"], expected["charge_adc_samples"], rtol=0, atol=1e-3)


def test_flags_are_decoded(reader, sample):
    path, expected = sample
    got = pd.read_csv(io.StringIO(_run(reader, path).stdout))
    assert got["flags"].tolist() == expected["flags"].tolist()


def test_missing_file_is_a_clean_error(reader, tmp_path):
    out = _run(reader, tmp_path / "does_not_exist.wfb1")
    assert 0 < out.returncode < 128, f"exit code {out.returncode} (>=128 means the program crashed)"
    assert out.stderr.strip(), "explain the error on stderr"


def test_truncated_file_is_a_clean_error(reader, sample, tmp_path):
    path, _ = sample
    bad = tmp_path / "truncated.wfb1"
    bad.write_bytes(path.read_bytes()[:-1000])
    out = _run(reader, bad)
    assert 0 < out.returncode < 128, f"exit code {out.returncode}"


def test_wrong_magic_is_rejected(reader, sample, tmp_path):
    path, _ = sample
    bad = tmp_path / "bad_magic.wfb1"
    raw = bytearray(path.read_bytes())
    raw[0:4] = b"XXXX"
    bad.write_bytes(bytes(raw))
    out = _run(reader, bad)
    assert 0 < out.returncode < 128
