# Lab 6 · Context and token efficiency, measured (30 min)

**Goal:** find out, with numbers, what project instructions and skills buy you in
cost and correctness on a real task.

## Part A · Watch the context fill (5 min)
In a session, run `/context`. Then ask Claude to read `src/wfkit/generator.py`
and run `/context` again. Then ask it to read every file under `src/` and check
once more. Try `/compact` and look again. Note what it kept.

Habits worth adopting:
- one task per session; `/clear` between unrelated tasks
- point at files by path instead of pasting them
- ask for a subagent to search a large codebase, so the search results stay out of your session
- put the stable facts in `CLAUDE.md` once, instead of retyping them

## Part B · Measure it (25 min)
`task.md` in this folder is a fixed task with an automatic acceptance check.
The tool runs it headless in fresh copies of the repository under three conditions:
no project context, `CLAUDE.md` only, and `CLAUDE.md` plus the skill.

```
uv run python tools/token_compare.py \
  --task labs/day2/lab6-context/task.md \
  --accept "uv run pytest tests/validation -q -m 'not advanced' --impl work.lab6:analyze" \
  --condition bare --condition claude_md --condition skill \
  --trials 2 --model sonnet
```

Each trial takes a few minutes. The room will pool results on the shared sheet.

## Tiers
- **Beginner:** run with `--trials 1`, record your row in the room's table.
- **Intermediate:** add a fourth condition of your own (a shorter `CLAUDE.md`, a different model, `--permission-mode auto`) by editing `prepare()` in the tool.
- **Advanced:** estimate how many trials you would need to tell a 20% cost difference from noise at your observed spread, and say whether the room's pooled data meets that.

## Acceptance
Your rows are in the room table, and you can state one conclusion the data
supports and one it does not.
