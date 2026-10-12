# Day 2 participant challenges

Work in pairs. Pick one challenge, or two if they are short. You have 60 minutes,
then you hand your work to another pair, who review it against the acceptance
criteria and your handoff note.

Every challenge needs, at the end:
- the work brief you started from (`templates/work-brief.md`)
- the evidence that it meets the acceptance criteria (test output, verification table)
- a handoff note with limitations (`templates/handoff-note.md`)

Each challenge lists a level, but every challenge has a Beginner path. Ask for help early.

| # | Challenge | Kind | Level | Checked by |
|---|-----------|------|-------|------------|
| C1 | Dark count rate and crosstalk | Python analysis | Intermediate | automatic, hidden dataset |
| C2 | Two-channel timing | Python analysis | Advanced | automatic, hidden dataset |
| C3 | Repair and modernise a C++ DAQ reader | C++ | Intermediate to Advanced | automatic |
| C4 | Waveform viewer you can hand to a student | local app | Beginner to Intermediate | peer review checklist |
| C5 | Onboarding guide for MIDAS or MERCI, every claim cited | code understanding | Beginner to Intermediate | peer verification |
| C6 | Research brief with provenance | non-coding | Beginner | peer verification |
| C7 | Your own build problem, triaged and pinned | C++ / build | Advanced | clean rebuild |
| C8 | A skill your group will use, with an evaluation | workflow | Intermediate | automatic + peer |
| C9 | PMT single-photoelectron calibration | Python analysis | Advanced | automatic |

---

## C1 · Dark count rate and crosstalk
`data/sipm_dark.parquet` is a random-trigger run with the LED off. Measure the
primary dark count rate (Hz) and the optical crosstalk probability.

Write `measure(path) -> {"dcr_hz": float, "crosstalk_prob": float}` and check it:

```
uv run pytest tests/challenges/test_dark_and_timing.py -k dark -v --dark-impl work.c1:measure
```

The check also runs your function on a hidden run with different, randomised
rates, so tuning to the shipped file will not pass. Tolerance: 5% on rate,
0.015 absolute on crosstalk.

*Beginner path:* plot 20 waveforms first and describe what you see before writing any analysis.
*Think about:* afterpulses look like dark counts. How do you avoid counting them, and what does that do to the live time?

## C2 · Two-channel timing
`data/coincidence.parquet` has two SiPMs viewing one scintillator, with a fixed
cable delay between them. Measure the delay (ns) with an uncertainty, and the
single-channel timing resolution.

`measure(path) -> {"delay_ns", "delay_err_ns", "resolution_ns"}`:

```
uv run pytest tests/challenges/test_dark_and_timing.py -k timing -v --timing-impl work.c2:measure
```

Tolerance on the delay: 0.05 ns, on the shipped run and on a hidden run with a random delay.
*Think about:* the sample period is 4 ns. A method can have a tiny statistical
error and still be biased. Show that your answer does not depend on a method
parameter you chose.

## C3 · Repair and modernise a C++ DAQ reader
`legacy/cpp/wfb1_reader.cpp` reads the raw format in `docs/wfb1-format.md`.
It compiles, runs, and is wrong. Make it pass:

```
uv run wfkit export-wfb1
uv run pytest tests/challenges/test_wfb1_reader.py -v
```

To test a binary built elsewhere: `uv run pytest ... --wfb1-reader path/to/binary`

*Intermediate:* all tests pass. *Advanced:* also no raw `new`/`delete`, no globals,
clean under `-Wall -Wextra -Werror` and `clang-tidy` (`modernize-*`, `bugprone-*`),
and a unit test (Catch2 or similar) for the header parser, and it passes the
hostile-input suite: `uv run pytest tests/security -v --wfb1-source <folder with your CMakeLists.txt>`.
This is the same class of problem as reading MIDAS banks or MERCI raw files.

## C4 · A waveform viewer you can hand to a student
A small local app (Streamlit is installed with `uv sync --extra app`, or a single
self-contained HTML page) that opens any run file and lets someone:
- step through events, showing the baseline window and gate from the metadata
- see the charge spectrum and click through to events in a chosen charge range
- overlay several events

*Peer review checklist:* a student who has never seen it can open a run and
find a two-photoelectron event in under two minutes, using only your README.
Units on every axis. Nothing hard-coded that the metadata provides.

## C5 · Onboarding guide for MIDAS or MERCI
Clone MIDAS or MERCI:

```
git clone --recursive https://gitlab.triumf.ca/midas/midas.git      # branch develop
git clone -b devel https://bitbucket.org/team-waveformers/merci.git
```

MIDAS needs `--recursive`: `manalyzer`, `midasio`, `mvodb`, `mjson`, `mxml` and
`mscb` are submodules, and without them the headers MERCI includes are missing.
MIDAS moved from Bitbucket to TRIUMF GitLab; older notes, and MERCI's own
README and CMake fallback, still point at Bitbucket. Produce
`docs/onboarding.md` for a new student: what the main components are, how data
flows from hardware to disk, how to build, and where to start reading.

Rule: every factual statement carries a `path:line` reference. Your reviewers
pick ten statements at random and check them. Target: ten out of ten.

*Beginner path:* start with "how do I build this, and what are the first three files to read?"
*Advanced:* add a diagram of the data path, and a list of the five places in the
code most likely to surprise a newcomer, each with the evidence.

Questions a good guide answers, each with a `path:line` (your reviewers will check):
- Where does MERCI get the sample period of a waveform, and is there more than one source for it?
- What happens when a required key is missing from a MERCI JSON config?
- Which C++ standard does MIDAS build with by default, and how do you change it?
- Where does a MERCI build get `manalyzer` from, with and without `$MIDASSYS` set?
- If both a `CLAUDE.md` and an `AGENTS.md` are present, which one does Claude Code read?

## C6 · Research brief with provenance
Lab 8, taken further: a question that matters to your own work, a brief in
`templates/research-brief.md` format, and a provenance table your reviewers can
spot-check. Reviewers open five sources at random.

## C7 · Your own build problem, triaged and pinned
Bring a real build failure (Geant4, ROOT, CUDA, a MERCI dependency). Only bring
material you are allowed to share with the tool. Use `templates/build-triage.md`.
Done means a clean build from scratch, and the working versions pinned in a
container definition (Apptainer `.def` or Dockerfile) or equivalent that a
colleague can rebuild.

Reference points for Geant4 (from the 11.4 release notes and top-level
`CMakeLists.txt`, checked 8 October 2026): CMake 3.16 or later (3.20 for C++23);
C++ standard 17, 20 or 23; tested with GCC 15.2 on Alma Linux 9, Clang 17 on
macOS and Visual Studio 2022, with GCC 11.5 to 14.2 also verified. Source:
https://github.com/Geant4/geant4 (official mirror of gitlab.cern.ch/geant4/geant4).
A mismatch between the C++ standard Geant4 was built with and the one your
application uses is a common cause of link errors; check it first.

MIDAS builds with C++20 by default (since September 2026; `-DMIDAS_CXX17_FALLBACK=ON`
gives C++17). Know which standard each of Geant4, ROOT, MIDAS and your own code was
built with before you start guessing at link errors.

## C8 · A skill your group will use, with an evaluation
Lab 7, taken further: the skill, plus three test prompts with checkable expected
outputs, run headless (`claude -p ... --output-format json`) and scored by a
script. Show the score with and without the skill.

## C9 · PMT single-photoelectron calibration
Make an analysis that passes the advanced check:

```
uv run pytest tests/validation -v --impl work.c9:analyze
```

including `test_pmt_gain_matches_truth` (5% tolerance). The PMT single-photoelectron
response is broad and close to the pedestal. Explain your model choice in the handoff note.
