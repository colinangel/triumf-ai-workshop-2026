"""Acceptance tests for challenges C1 (dark counts) and C2 (two-channel timing).

Point the tests at your function with an environment variable:

    uv run pytest tests/challenges/test_dark_and_timing.py -k dark -v --dark-impl mywork.dark:measure
    uv run pytest tests/challenges/test_dark_and_timing.py -k timing -v --timing-impl mywork.timing:measure

C1 function: f(path) -> {"dcr_hz": float, "crosstalk_prob": float}
C2 function: f(path) -> {"delay_ns": float, "delay_err_ns": float, "resolution_ns": float}

Each is checked on the shipped dataset and on a hidden one generated here with
randomised parameters, so a result tuned to the shipped file will not pass.
"""

from __future__ import annotations

import dataclasses
import importlib
import os
import secrets
import sys
from pathlib import Path

import pytest

from wfkit.config import PRESETS
from wfkit.generator import generate
from wfkit.io import write_run

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _impl(var):
    spec = os.environ.get(var)
    if not spec:
        pytest.skip(f"set {var}=module:function to check your solution")
    mod, _, fn = spec.partition(":")
    return getattr(importlib.import_module(mod), fn)


def _hidden(tmp_path, cfg, name):
    path = tmp_path / name
    write_run(generate(cfg, n_events=cfg.default_events, seed=secrets.randbelow(10**6)), path)
    return path.with_suffix(".parquet")


# --- C1: dark counts ----------------------------------------------------------


def _check_dark(result, cfg):
    s = cfg.sensor
    assert result["dcr_hz"] == pytest.approx(s.dark_rate_hz, rel=0.05), f"DCR {result['dcr_hz']:.4g} Hz vs truth {s.dark_rate_hz:.4g} Hz"
    assert result["crosstalk_prob"] == pytest.approx(s.crosstalk_prob, abs=0.015), (
        f"crosstalk {result['crosstalk_prob']:.4f} vs truth {s.crosstalk_prob:.4f}"
    )


def test_dark_counts_on_shipped_run():
    f = _impl("WFKIT_DARK")
    path = ROOT / "data" / "sipm_dark.parquet"
    if not path.exists():
        write_run(generate(PRESETS["sipm_dark"]), path.with_suffix(""))
    _check_dark(f(str(path)), PRESETS["sipm_dark"])


def test_dark_counts_on_hidden_run(tmp_path):
    f = _impl("WFKIT_DARK")
    rng = secrets.SystemRandom()
    base = PRESETS["sipm_dark"]
    sensor = dataclasses.replace(base.sensor, dark_rate_hz=rng.uniform(150e3, 600e3), crosstalk_prob=rng.uniform(0.05, 0.22))
    cfg = dataclasses.replace(base, sensor=sensor)
    _check_dark(f(str(_hidden(tmp_path, cfg, "dark"))), cfg)


# --- C2: timing ---------------------------------------------------------------


def _check_timing(result, cfg):
    truth = cfg.channel_delays_ns[1] - cfg.channel_delays_ns[0]
    assert result["delay_ns"] == pytest.approx(truth, abs=0.05), f"delay {result['delay_ns']:.3f} ns vs truth {truth:.3f} ns"
    assert 0 < result["delay_err_ns"] < 0.05, "report a statistical uncertainty on the delay"
    assert 0.05 < result["resolution_ns"] < 2.0, "per-channel resolution should be physically sensible"


def test_timing_on_shipped_run():
    f = _impl("WFKIT_TIMING")
    path = ROOT / "data" / "coincidence.parquet"
    if not path.exists():
        write_run(generate(PRESETS["coincidence"]), path.with_suffix(""))
    _check_timing(f(str(path)), PRESETS["coincidence"])


def test_timing_on_hidden_run(tmp_path):
    f = _impl("WFKIT_TIMING")
    delay = round(secrets.SystemRandom().uniform(-6.0, 6.0), 3)
    cfg = dataclasses.replace(PRESETS["coincidence"], channel_delays_ns=(0.0, delay), default_events=5000)
    _check_timing(f(str(_hidden(tmp_path, cfg, "timing"))), cfg)
