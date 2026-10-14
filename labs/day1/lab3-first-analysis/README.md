# Lab 3 · Plan, build, test: a first real result (75 min)

**Goal:** a gain calibration for the SiPM, built by directing Claude Code with a
written brief, checked against acceptance criteria you wrote before any code existed.

Data: `data/sipm_lowlight.parquet` (20,000 LED triggers, about 1.5 photoelectrons each).
Run `uv run wfkit info data/sipm_lowlight.parquet` first and read it.

**Before you start:** this lab runs on **Opus at high effort**, for the whole lab. Set both before
your first prompt (Lab 1, step 3 shows where in your surface).

## 1. Write the brief (15 min, no code yet)

**First, read what the agent already knows (3 min).** Every session in this folder reads
`CLAUDE.md`: the environment, the data rules, how to work. The waveform-analysis skill
(`.claude/skills/waveform-analysis/SKILL.md`) loads for this kind of task: baseline, charge, gain
fit, cuts. Don't repeat either in your brief. Write each layer of context once, where it lives.

**Then write only the task (12 min).** Copy `templates/work-brief.md` to `work/lab3-brief.md`.
For each heading, ask: what does this task need that those two files don't already say?

- **Goal:** the charge spectrum and the gain (pC per photoelectron, and electrons) for this run,
  with an uncertainty, and what the result is for.
- **Context:** what's specific to this run and this check. Two places to look:
  - `data/sipm_lowlight.json`: open it. Some keys are the generator's true values. `CLAUDE.md`
    rules out the truth files but says nothing about these.
  - `tests/validation/test_against_truth.py`: each test's name, and the comment under most of
    them, says how the result is judged. Note which runs it uses.
- **Acceptance criteria** you can check. Suggested starting set:
  - [ ] a function `analyze(path) -> dict` returning the keys listed in `tests/validation/conftest.py`
  - [ ] `uv run pytest tests/validation -v -m "not advanced" --impl work.lab3:analyze` passes
  - [ ] a log-scale charge spectrum, axes with units, saved to `results/lab3_spectrum.png`
  - [ ] gain reported with an uncertainty
- **Constraints, Out of scope, Deliverables:** a line each, or "none beyond `CLAUDE.md`".

You can ask Claude to help you read these files or tidy your wording, but write the acceptance
criteria yourself: they are how you will judge its work.

Swap briefs with your neighbour for two minutes. What would they have guessed wrong?

## 2. Plan (10 min)
Start a new session in Plan mode, on Opus at high effort, and give it your brief: *"Read work/lab3-brief.md and propose a plan. Do not write code yet."*
Push back on anything vague. Approve when the plan names how each acceptance criterion will be checked.

## 3. Build and test (30 min)
Approve the plan, choose Auto mode, and watch the tool calls rather than the summary. Expect tests
first, then the analysis, then a validation run.

- Ask to see the validation output itself, not a description of it.
- When a test fails, ask what the failure means physically before accepting a fix. If the fix is a
  new cut, check that it looks only at samples before the gate.
- Never accept a change to `tests/validation/`.
- Still failing at 20 minutes? Ask a helper.

## 4. Check one thing yourself (5 min)
Pick one event. Ask for the raw ADC sum in the gate, then apply each conversion
factor yourself. Does your number match the code's?

## 5. Write it up for your group (15 min)
A result nobody can read is not finished. Turn yours into the two things you would
actually hand over:

1. **A one-page result note.** In Claude Code: *"Fill in templates/result-note.md as
   work/lab3-result.md from the validation output, the fit result and the plot. Quote
   every number from a command you run now, not from earlier in this session."*
   This is what creates `work/lab3-result.md`; the build in step 3 doesn't.
2. **Three slides for a group meeting.** In the Claude app, start a new chat, attach
   the note you just made (`work/lab3-result.md`) and `results/lab3_spectrum.png`, and ask for a three-slide
   deck: the result, how it was checked, what it does not cover. If your organisation
   has Claude Slides switched on, it builds an editable deck you can export to
   PowerPoint; otherwise ask for the slide text and paste it into your usual template.

Then check it like a referee: every number on the slides must match your test output,
with the same units and uncertainty. Mark anything that does not.

## Tiers
- **Beginner:** criteria above. If stuck, ask Claude to explain each failing test in plain language before fixing.
- **Intermediate:** add a test of your own that would catch a hard-coded sample period, and show it fails if you hard-code one.
- **All tiers:** step 5. You will show your slides at the end of the day.
- **Advanced:** make the analysis also pass `test_pmt_gain_matches_truth` (run with `-m advanced`). The PMT single-photoelectron peak is broad and close to the pedestal; you will need a different fit model. Explain in two sentences why the SiPM model fails there.

## Acceptance
Validation passes; your brief, plan, code and result note are in `work/`; your three
slides state the gain with its uncertainty and how you know it is right, and every
number on them matches the test output.

## Debrief question
Which of your acceptance criteria caught something? Which one did you wish you had written?
Did any number change between your test output and the slides?
