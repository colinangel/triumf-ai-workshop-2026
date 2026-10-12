"""Files written by wfkit must round-trip without loss in every supported format."""

import json

import numpy as np
import pytest

from wfkit.config import PRESETS
from wfkit.generator import generate
from wfkit.io import read_run, write_run


@pytest.fixture(scope="module")
def run():
    return generate(PRESETS["coincidence"], n_events=300, seed=21)


@pytest.mark.parametrize("fmt", ["parquet", "root"])
def test_round_trip(tmp_path, run, fmt):
    paths = write_run(run, tmp_path / "r", formats=(fmt,))
    back = read_run(paths[fmt])
    assert np.array_equal(back.waveforms, run.waveforms)
    stored = {k: v for k, v in back.metadata.items() if k != "sha256"}
    assert stored == json.loads(json.dumps(run.metadata))


def test_truth_and_metadata_sidecars(tmp_path, run):
    paths = write_run(run, tmp_path / "r", formats=("parquet",))
    assert paths["truth"].exists() and paths["pe"].exists() and paths["metadata"].exists()
    md = json.loads(paths["metadata"].read_text())
    assert md["n_events"] == 300
    assert "sha256" in md and set(md["sha256"]) >= {"truth"}


def test_binary_export_layout(tmp_path, run):
    """The WFB1 binary is the input for the C++ challenge; pin its layout."""
    from wfkit.io import WFB1_EVENT_HEADER, WFB1_FILE_HEADER, write_wfb1

    path = write_wfb1(run, tmp_path / "r.wfb1")
    raw = path.read_bytes()
    n_ch, n_ev, n_s = run.waveforms.shape
    expected = WFB1_FILE_HEADER.size + n_ev * (WFB1_EVENT_HEADER.size + n_ch * n_s * 2)
    assert len(raw) == expected
    magic, _version, n_channels, n_samples, dt_ps, n_events = WFB1_FILE_HEADER.unpack_from(raw, 0)
    assert magic == b"WFB1" and n_channels == n_ch and n_samples == n_s and n_events == n_ev
    assert dt_ps == 4000
