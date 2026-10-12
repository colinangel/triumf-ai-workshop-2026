"""Reading and writing runs: Parquet (default), ROOT via uproot, and a raw binary.

A run on disk is a set of files sharing a stem:
  <stem>.parquet     waveforms (one fixed-length int16 list column per channel)
  <stem>.root        the same waveforms as a TTree named "events" (optional)
  <stem>.truth.parquet  one row per (event, channel): photoelectron counts, true charges
  <stem>.pe.parquet     one row per photoelectron
  <stem>.json           run metadata: units, digitizer settings, seed, checksums

The truth and pe files are the answer key. Analysis code should read only the
waveform file and the metadata unless it is explicitly validating against truth.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# WFB1: little-endian, deliberately unpadded ("packed") records.
WFB1_FILE_HEADER = struct.Struct("<4sHHIIQ")  # magic, version, n_channels, n_samples, dt_ps, n_events
WFB1_EVENT_HEADER = struct.Struct("<IHQ")  # event_id, flags (bit c = channel c saturated), trigger_time_ps


@dataclass
class LoadedRun:
    waveforms: np.ndarray  # (n_channels, n_events, n_samples)
    metadata: dict
    event: np.ndarray
    truth: pd.DataFrame | None = None


def checksums(run) -> dict[str, str]:
    t = run.truth
    counts = np.stack([t[c].to_numpy(np.int64) for c in ("event", "channel", "n_primary", "n_crosstalk", "n_afterpulse", "n_dark")])
    return {
        "truth": hashlib.sha256(counts.astype("<i8").tobytes()).hexdigest(),
        "waveforms": hashlib.sha256(run.waveforms.astype("<i2").tobytes()).hexdigest(),
    }


def write_run(run, stem: str | Path, formats=("parquet",)) -> dict[str, Path]:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    n_ch, n_ev, n_s = run.waveforms.shape
    md = dict(run.metadata, sha256=checksums(run))
    paths: dict[str, Path] = {}

    if "parquet" in formats:
        cols = {"event": pa.array(np.arange(n_ev, dtype=np.int64))}
        for c in range(n_ch):
            flat = pa.array(run.waveforms[c].reshape(-1), type=pa.int16())
            cols[f"wf_ch{c}"] = pa.FixedSizeListArray.from_arrays(flat, n_s)
        table = pa.table(cols).replace_schema_metadata({"wfkit": json.dumps(md)})
        paths["parquet"] = stem.with_suffix(".parquet")
        pq.write_table(table, paths["parquet"], compression="zstd")

    if "root" in formats:
        import uproot

        paths["root"] = stem.with_suffix(".root")
        with uproot.recreate(paths["root"]) as f:
            branches = {"event": np.arange(n_ev, dtype=np.int64)}
            for c in range(n_ch):
                branches[f"wf_ch{c}"] = run.waveforms[c]
            f["events"] = branches
            f["metadata"] = json.dumps(md)

    paths["truth"] = stem.with_name(stem.name + ".truth.parquet")
    run.truth.to_parquet(paths["truth"], index=False)
    paths["pe"] = stem.with_name(stem.name + ".pe.parquet")
    run.pe.to_parquet(paths["pe"], index=False)
    paths["metadata"] = stem.with_suffix(".json")
    paths["metadata"].write_text(json.dumps(md, indent=2) + "\n")
    return paths


def read_run(path: str | Path, with_truth: bool = False) -> LoadedRun:
    path = Path(path)
    if path.suffix == ".parquet":
        table = pq.read_table(path)
        md = json.loads(table.schema.metadata[b"wfkit"])
        n_s = md["n_samples"]
        chans = sorted(c for c in table.column_names if c.startswith("wf_ch"))
        wf = np.stack([table[c].combine_chunks().flatten().to_numpy().reshape(-1, n_s) for c in chans])
        event = table["event"].to_numpy()
    elif path.suffix == ".root":
        import uproot

        with uproot.open(path) as f:
            md = json.loads(str(f["metadata"]))
            tree = f["events"]
            chans = sorted(k for k in tree.keys() if k.startswith("wf_ch"))  # noqa: SIM118 (uproot TTree, not a dict)
            arrays = tree.arrays(["event", *chans], library="np")
        wf = np.stack([arrays[c] for c in chans]).astype(np.int16)
        event = arrays["event"]
    else:
        raise ValueError(f"unsupported waveform file: {path}")

    truth = None
    if with_truth:
        truth = pd.read_parquet(path.with_name(path.stem + ".truth.parquet"))
    return LoadedRun(waveforms=wf, metadata=md, event=event, truth=truth)


def write_wfb1(run, path: str | Path) -> Path:
    """Raw binary in the style of a DAQ dump, used by the C++ challenge."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n_ch, n_ev, n_s = run.waveforms.shape
    dt_ps = round(run.metadata["dt_ns"] * 1000)
    sat = run.truth.pivot(index="event", columns="channel", values="saturated").to_numpy()
    trig_ps = round(run.metadata["trigger_sample"] * run.metadata["dt_ns"] * 1000)
    with path.open("wb") as f:
        f.write(WFB1_FILE_HEADER.pack(b"WFB1", 1, n_ch, n_s, dt_ps, n_ev))
        for e in range(n_ev):
            flags = int(sum(1 << c for c in range(n_ch) if sat[e, c]))
            f.write(WFB1_EVENT_HEADER.pack(e, flags, trig_ps + e * 1_000_000))
            f.write(run.waveforms[:, e, :].astype("<u2").tobytes())
    return path
