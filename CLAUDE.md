# Project instructions: TRIUMF AI workshop kit

This file is read by Claude Code at the start of every session in this folder.
It is also a worked example: Day 1 compares sessions with and without it.

## What this repository is

Synthetic SiPM and PMT waveform data with full ground truth (`src/wfkit`), a
legacy analysis script with known problems (`legacy/`), and tests that compare
any analysis to the truth (`tests/validation`).

## Environment

- Python is managed by uv. Run everything as `uv run ...`. Do not pip install.
- Regenerate data with `uv run wfkit generate --all`. Data is deterministic from the seed.
- C++ code builds with CMake (`cmake -S legacy/cpp -B build/cpp && cmake --build build/cpp`).

## Data rules

- Analysis code reads the waveform file (`data/<run>.parquet` or `.root`) and its
  metadata only. `*.truth.parquet` and `*.pe.parquet` are the answer key: use them
  in tests and validation, never inside an analysis.
- Units and settings come from the run metadata (`wfkit info <file>`): sample
  period, ADC scale, impedance, preamplifier gain, polarity, gate, baseline window.
  Never hard-code them.
- Charge is reported in pC at the sensor. Gain is in electrons per photoelectron.

## How to work

1. Restate the task and the acceptance criteria before writing code. If the criteria
   are missing, ask.
2. Write or update a test that fails for the right reason before changing analysis code.
3. Run the relevant tests and show the output. "Should work" is not evidence.
4. When a result is a number, give its uncertainty and say how it was checked.
5. Keep changes small and reviewable. Do not refactor unrelated code.

## Commands

- Unit tests: `uv run pytest`
- Validate an analysis against truth: `uv run pytest tests/validation -v --impl module:function`
- Challenge checks: see `challenges/README.md`

## Do not

- Edit files under `tests/` to make a failing check pass, unless asked to change the check itself.
- Read truth files from analysis code.
- Delete or overwrite anything in `data/raw/`.
