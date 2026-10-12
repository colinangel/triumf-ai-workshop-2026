# Lab 7 · Write a skill your group would actually use (30 min)

**Goal:** capture one piece of your group's working knowledge as a skill, test
that it changes behaviour, and know how to share it.

**Before you start:** use **Sonnet at medium effort** for every test run, before and after you revise the
skill, so a change in behaviour comes from the skill: `claude --model sonnet --effort medium`.

## 1. Pick the knowledge (5 min)
Good candidates are things a new student gets wrong in their first month:
- how your experiment's run files are named and where they live
- which calibration constants are current, and where they are recorded
- how to build your code on the cluster (modules to load, compiler, flags)
- the checks your group always runs before showing a plot
- how to read a MIDAS bank, or a MERCI configuration, for your setup

## 2. Write it (12 min)
Copy `templates/skill-template/` to `.claude/skills/<your-skill-name>/` and fill it in.
Keep `SKILL.md` under about 100 lines; link to longer reference files.
The `description` line decides when it loads: name the tasks and file types.

## 3. Test it (10 min)
Write two prompts in `work/lab7-tests.md`:
- one that **should** use the skill, with what a correct answer must contain
- one that **should not**

Run both in fresh sessions. Did the skill load when it should, and stay out when it should not? Did the answer meet your criteria? Revise and rerun once.

## 4. Share it (3 min)
Three ways, in order of reach:
- commit `.claude/skills/<name>/` to your group's repository (everyone who clones it gets it in Claude Code)
- put it in `~/.claude/skills/` for yourself across all projects
- ask your Claude Enterprise owner to add it for the organisation (it then appears in the Claude app and syncs to Claude Code)

## Tiers
- **Beginner:** a skill with conventions and a checklist; both test prompts behave.
- **Intermediate:** add a script the skill tells Claude to run (for example a units check) and show it being run.
- **Advanced:** give the skill an evaluation: three prompts with checkable expected outputs, run headless with `claude -p --model sonnet --effort medium`, scored automatically.

## Acceptance
The skill folder exists, the two test prompts behave as intended, and you have
named who in your group would maintain it.
