# Lab 4 · Skills: domain context on demand (40 min)

**Goal:** see what a skill changes, by running the same task with and without one.

A skill is a folder with a `SKILL.md`: a short description that Claude always sees,
and instructions it loads only when a request matches. This repository ships one:
`.claude/skills/waveform-analysis/SKILL.md`. Read it now (3 min).

**Before you start:** use **Sonnet at medium effort** for both runs, and change nothing else between them,
or the comparison means nothing. Set both at the start of each session (Lab 1, step 3 shows where in your surface).

## 1. Without the skill
Move the skill folder aside: `mv .claude/skills .claude/skills_off`

In a **new** session, on Sonnet at medium effort:

> Write `work/lab4_off.py` with a function `analyze(path)` that measures the SiPM gain
> from a waveform file. Return the keys required by tests/validation/conftest.py.

Run `uv run pytest tests/validation -v -m "not advanced" --impl work.lab4_off:analyze`.
Record: tests passed, turns taken, session cost.

## 2. With the skill
Restore it: `mv .claude/skills_off .claude/skills`. New session, same prompt but
writing `work/lab4_on.py`. Did Claude say it was using the skill? Run the same tests with `--impl work.lab4_on:analyze`. Record the same numbers.

## 3. Compare
| | Tests passed | Turns | Cost | What it did differently |
|-|-------------:|------:|-----:|-------------------------|
| Without skill | | | | |
| With skill | | | | |

One run each is an anecdote. Compare with the table at your neighbours'.

## Tiers
- **Beginner:** steps 1 to 3.
- **Intermediate:** add one convention your own group uses to the skill (a naming rule, a unit, a cut you always apply). Rerun step 2. Did it follow it?
- **Advanced:** make the skill trigger less often by mistake: write a request that should *not* load it and check that it does not. Then tighten the `description` line until both cases behave.

## Acceptance
The comparison table is filled in, and you can say which part of the skill made the difference, if any.

## Debrief question
What would go in a skill for your own experiment, and who would maintain it?
