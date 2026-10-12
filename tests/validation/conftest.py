"""Shared fixtures for validating an analysis against ground truth.

Choose the analysis under test with --impl module.path:function (or the
WFKIT_IMPL environment variable; default: legacy.analyze_run:analyze). The function must accept a waveform file
path and return a dict with at least:

    event             int array, event ids
    charge_pc         float array, per-event charge at the sensor in pC (every event)
    selected          bool array, events the analysis keeps
    gain_pc           float, single-photoelectron charge in pC
    gain              float, gain in electrons per photoelectron
    pedestal_pc       float, position of the zero-photoelectron peak in pC
    mean_npe_in_gate  float, mean photoelectrons per trigger in the gate
"""

from __future__ import annotations

import contextlib
import importlib
import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wfkit.config import PRESETS
from wfkit.generator import generate
from wfkit.io import write_run

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = ["event", "charge_pc", "selected", "gain_pc", "gain", "pedestal_pc", "mean_npe_in_gate"]


def _load_impl():
    spec = os.environ.get("WFKIT_IMPL", "legacy.analyze_run:analyze")
    module, _, func = spec.partition(":")
    return spec, getattr(importlib.import_module(module), func or "analyze")


@pytest.fixture(scope="session")
def impl():
    return _load_impl()[1]


@pytest.fixture(scope="session")
def data_dir() -> Path:
    d = Path(os.environ.get("WFKIT_DATA", ROOT / "data"))
    for name in ("sipm_lowlight", "sipm_highlight", "pmt_spe"):
        if not (d / f"{name}.parquet").exists():
            write_run(generate(PRESETS[name]), d / name)
    return d


class Case:
    """An analysis result paired with the truth for the same run."""

    def __init__(self, name: str, result: dict, truth: pd.DataFrame, pe: pd.DataFrame):
        self.name = name
        self.cfg = PRESETS[name]
        self.r = result
        self.truth = truth.sort_values("event").reset_index(drop=True)
        self.pe = pe
        missing = [k for k in REQUIRED if k not in result]
        if missing:
            raise AssertionError(f"analysis result is missing keys: {missing}")
        order = np.argsort(np.asarray(result["event"]))
        self.event = np.asarray(result["event"])[order]
        self.q = np.asarray(result["charge_pc"], dtype=float)[order]
        self.sel = np.asarray(result["selected"], dtype=bool)[order]
        if not np.array_equal(self.event, self.truth["event"].to_numpy()):
            raise AssertionError("analysis must return one charge per event, for every event in the file")

    @property
    def q1(self) -> float:
        return self.cfg.q1_pc

    @property
    def finger_spacing_pc(self) -> float:
        """True single-PE charge contained in the standard gate for prompt light."""
        p = self.cfg.sensor.pulse
        t0 = self.cfg.trigger_time_ns + self.cfg.light.offset_ns
        lo, hi = self.cfg.standard_gate_ns
        return self.cfg.q1_pc * float(p.cdf(hi - t0) - p.cdf(lo - t0))


def _run_case(impl, data_dir: Path, name: str) -> Case:
    path = data_dir / f"{name}.parquet"
    with contextlib.redirect_stdout(io.StringIO()):
        result = impl(str(path))
    return Case(name, result, pd.read_parquet(data_dir / f"{name}.truth.parquet"), pd.read_parquet(data_dir / f"{name}.pe.parquet"))


@pytest.fixture(scope="session")
def lowlight(impl, data_dir) -> Case:
    return _run_case(impl, data_dir, "sipm_lowlight")


@pytest.fixture(scope="session")
def highlight(impl, data_dir) -> Case:
    return _run_case(impl, data_dir, "sipm_highlight")


@pytest.fixture(scope="session")
def pmt(impl, data_dir) -> Case:
    return _run_case(impl, data_dir, "pmt_spe")


def pytest_report_header(config):
    return f"analysis under test: {_load_impl()[0]}"
