# AI and agentic tools for scientific work: TRIUMF workshop kit

Two days, 16 and 19 October 2026. This repository is everything you work with
during the hands-on sessions.

**Before the workshop:** install git, uv and Claude Code with [`setup/SETUP.md`](setup/SETUP.md).
**Day 1:** Lab 1 clones this repository and runs `uv run python setup/check_setup.py`.

## What is here

| Path | What it is |
|------|------------|
| `src/wfkit/` | Simulator for SiPM and PMT waveforms with full ground truth: Poisson light, gain spread, crosstalk, afterpulsing, dark counts, noise, pedestal drift, ADC quantisation and saturation |
| `data/` | Generated runs (`uv run wfkit generate --all`). Each run: waveforms (`.parquet`, optionally `.root`), metadata (`.json`), and the answer key (`.truth.parquet`, `.pe.parquet`) |
| `legacy/` | Analysis code with problems: a Python gain analysis and a C++ raw-data reader |
| `tests/unit/` | Tests of the simulator itself |
| `tests/validation/` | Compares any charge analysis to the ground truth |
| `tests/challenges/` | Automatic checks for the Day 2 challenges, including hidden datasets |
| `tests/security/` | Hostile-input tests for the C++ reader, built with sanitizers (Lab S) |
| `labs/` | Lab instructions, each with Beginner, Intermediate and Advanced tracks |
| `challenges/` | Day 2 challenge briefs |
| `templates/` | Work brief, result note, handoff note, validation checklist, research brief, build triage, skill template |
| `.claude/skills/` | An example skill with waveform analysis conventions |
| `CLAUDE.md` | Project instructions Claude Code reads in this folder (also a worked example) |
| `docs/` | WFB1 raw format, the frontier reference sheet, and the security reference sheet, each with sources |
| `tools/token_compare.py` | Runs one task under several context conditions and compares cost and correctness |
| `work/` | Your code goes here |

## The datasets

| Run | Sensor | What it is for |
|-----|--------|----------------|
| `sipm_lowlight` | SiPM | resolved photoelectron peaks, gain calibration |
| `sipm_highlight` | SiPM | about 14 photoelectrons per trigger: linearity, amplitude-dependent effects |
| `sipm_dark` | SiPM | LED off, random trigger: dark counts, crosstalk, afterpulses |
| `pmt_spe` | PMT | single photoelectron response, broad and close to the pedestal |
| `coincidence` | 2 x SiPM | relative timing with a known cable delay |

Digitiser: 250 MS/s (4 ns per sample), 14 bit, 2 V peak to peak, 512 samples,
negative-going pulses. Look at any run with `uv run wfkit info data/<run>.parquet`.

Data are synthetic, so every number you measure can be checked against what the
simulation actually did. That is the point: you can find out whether a method
works before you trust it on real data.

## Common commands

```
uv sync                                   # install everything
uv run wfkit generate --all               # (re)create data/
uv run pytest                             # simulator unit tests
uv run pytest tests/validation -v         # validate the legacy analysis (fails, by design)
uv run pytest tests/validation -v --impl work.lab3:analyze   # validate yours
uv run pytest tests/security -v           # C++ reader vs hostile input (fails on legacy, by design)
```

## Licence
MIT. Reuse it for your own group's training.
