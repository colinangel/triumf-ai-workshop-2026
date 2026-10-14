# Lab 4 · Skills: domain context on demand (40 min)

**Goal:** see what a skill changes, by running the same task with and without one.

A skill is a folder with a `SKILL.md`: a short description that Claude always sees,
and instructions it loads only when a request matches. This repository ships one:
`.claude/skills/waveform-analysis/SKILL.md`. Read it now (3 min).

**Before you start:** use **Sonnet at medium effort** for both runs, and change nothing else between them,
or the comparison means nothing. Set both at the start of each session (Lab 1, step 3 shows where in your surface).

## 1. Without the skill
1. Close any open session in this repository.
2. Move the skill folder aside: `mv .claude/skills .claude/skills_off`
3. Start a **new** session and set Sonnet at medium effort.
4. Paste this prompt:

   > Write `work/lab4_off.py` with a function `analyze(path)` that measures the SiPM gain
   > from a waveform file. Return the keys required by tests/validation/conftest.py.
   > Work from the data and the tests only: don't open or copy code from other labs,
   > `work/` or `results/`.

5. Let it finish. If it asks a question, answer it; count each message you send as a turn.
   If you see it open another lab's code anyway, note it in the table: that run is not a fair comparison.
6. Run the tests:
   `uv run pytest tests/validation -v -m "not advanced" --impl work.lab4_off:analyze`
7. Record tests passed, turns and session cost (`/usage`, or the usage ring in the desktop app).

## 2. With the skill
1. Close the session from step 1.
2. Restore the skill: `mv .claude/skills_off .claude/skills`
3. Start a **new** session and set Sonnet at medium effort.
4. Paste the same prompt, with `work/lab4_on.py` in place of `work/lab4_off.py`.
5. Watch for Claude saying it is using the `waveform-analysis` skill. Count turns as before.
6. Run the tests:
   `uv run pytest tests/validation -v -m "not advanced" --impl work.lab4_on:analyze`
7. Record the same numbers.

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
