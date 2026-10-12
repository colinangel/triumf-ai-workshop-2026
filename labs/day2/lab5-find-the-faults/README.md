# Lab 5 · Find the faults: test-driven repair of legacy code (75 min)

**Goal:** make `legacy/analyze_run.py` give correct answers, proving each fix with
a test that failed before it and passes after.

The script is typical of code that has been passed between students for years.
It runs, produces a plausible-looking spectrum and a believable gain. It is wrong
in several independent ways. We will not tell you how many.

**Before you start:** this lab runs on **Opus at high effort**. Start Claude Code with
`claude --model opus --effort high`, or type `/model opus` and `/effort high` in a running session.

## 1. See the symptoms (10 min)

```
uv run python legacy/analyze_run.py data/sipm_lowlight.parquet
uv run pytest tests/validation -v
```

The validation suite compares the script to the simulation's ground truth. Read
each failure message. Before asking Claude anything, write down in `work/lab5-notes.md`
your own guess at what each failing test is telling you physically.

## 2. One fault at a time (55 min)
For each fault:

1. **Hypothesis:** what is wrong, and which test should change when it is fixed.
2. **Failing test first:** a small unit test in `tests/lab5/` that isolates this one fault
   and fails on the current code. It must fail for the reason you think.
3. **Fix:** the smallest change that makes your test pass.
4. **Evidence:** rerun `uv run pytest tests/validation -v`. Record which checks changed.
5. **Commit** with a message naming the fault and the test.

Good prompts for Claude here are narrow: *"Here is the failing check and the
function. What physical effect would produce exactly this symptom?"* Bad prompts
are wide: *"Fix the script."*

Expect a fix to expose another problem. That is information, not a setback.

## Tiers
- **Beginner:** work with Claude to find and test three faults. Use the skill
  (`.claude/skills/waveform-analysis`) as a checklist of what to suspect.
- **Intermediate:** all core validation checks pass. Every fix has its own test and commit.
- **Advanced:** as Intermediate, then refactor the script into a tested module
  (`work/lab5/`) with no globals, units from metadata, and a CLI. Make
  `test_pmt_gain_matches_truth` pass too. Write the handoff note.

## Rules
- Do not edit `tests/validation/` to make it pass.
- Do not read truth files from the analysis.
- "Claude said it is fixed" is not evidence. Test output is.

## Acceptance
`uv run pytest tests/validation -v -m "not advanced"` passes with the default
`WFKIT_IMPL` (the legacy script), your `tests/lab5/` tests pass, and your notes list
each fault: symptom, cause, test, fix.

## Debrief questions
- Which fault produced a number you would have believed?
- Which check would you add to your own group's analysis tomorrow?
