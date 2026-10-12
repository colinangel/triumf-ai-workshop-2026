"""Command line: `wfkit generate`, `wfkit info`, `wfkit export-wfb1`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wfkit.config import PRESETS
from wfkit.generator import generate
from wfkit.io import read_run, write_run, write_wfb1


def _generate(args) -> int:
    names = list(PRESETS) if args.all else args.preset
    if not names:
        print("choose --preset NAME (repeatable) or --all; presets: " + ", ".join(PRESETS), file=sys.stderr)
        return 2
    formats = tuple(f.strip() for f in args.formats.split(","))
    for name in names:
        cfg = PRESETS[name]
        run = generate(cfg, n_events=args.events, seed=args.seed)
        paths = write_run(run, Path(args.out) / name, formats=formats)
        print(
            f"{name:15s} {run.waveforms.shape[1]:6d} events x {run.waveforms.shape[0]} ch -> " + ", ".join(str(p) for p in paths.values())
        )
    return 0


def _info(args) -> int:
    run = read_run(args.path)
    md = run.metadata
    keep = [
        "preset",
        "description",
        "n_events",
        "n_channels",
        "sensor_kind",
        "dt_ns",
        "n_samples",
        "trigger_sample",
        "mv_per_adc",
        "impedance_ohm",
        "preamp_gain",
        "polarity",
        "standard_gate_ns",
        "standard_baseline_samples",
        "seed",
        "generator_version",
    ]
    print(json.dumps({k: md[k] for k in keep}, indent=2))
    return 0


def _wfb1(args) -> int:
    cfg = PRESETS[args.preset]
    run = generate(cfg, n_events=args.events, seed=args.seed)
    out = write_wfb1(run, Path(args.out))
    write_run(run, Path(args.out).with_suffix(""), formats=("parquet",))
    print(f"wrote {out} ({out.stat().st_size} bytes) and matching parquet/truth files")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wfkit", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate synthetic runs")
    g.add_argument("--preset", action="append", choices=list(PRESETS))
    g.add_argument("--all", action="store_true")
    g.add_argument("--out", default="data")
    g.add_argument("--formats", default="parquet", help="comma list of parquet,root")
    g.add_argument("--events", type=int, default=None, help="override the preset's event count")
    g.add_argument("--seed", type=int, default=None, help="override the preset's seed")
    g.set_defaults(func=_generate)

    i = sub.add_parser("info", help="print run metadata")
    i.add_argument("path")
    i.set_defaults(func=_info)

    w = sub.add_parser("export-wfb1", help="write a raw WFB1 binary for the C++ challenge")
    w.add_argument("--preset", default="sipm_lowlight", choices=list(PRESETS))
    w.add_argument("--events", type=int, default=2000)
    w.add_argument("--seed", type=int, default=None)
    w.add_argument("--out", default="data/raw/run_sipm.wfb1")
    w.set_defaults(func=_wfb1)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
