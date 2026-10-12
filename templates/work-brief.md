# Work brief

Fill this in before you ask an agent to do anything that takes more than a few minutes.
Paste it as your first message, or save it next to the code and point the agent at it.

## Goal
One or two sentences: what result, for whom, and what decision it feeds.

> Example: Measure the SiPM gain from `data/sipm_lowlight.parquet` so the
> high-light run can be converted to photoelectrons for the linearity study.

## Context the agent cannot guess
- Domain: (detector, sensor, physics conventions, units)
- System: (repo, language, environment, how to run things)
- Prior work: (scripts, slides, papers, a colleague's notebook; give paths or links)

## Constraints
- Must: (use run metadata for units; keep existing function signatures; ...)
- Must not: (read truth files; touch `data/raw/`; add dependencies without asking; ...)
- Permissions: (which data may leave the machine, which tools may run)

## Acceptance criteria
Each one checkable by someone who did not do the work.
- [ ] (for example: `uv run pytest tests/validation -v` passes with --impl ...)
- [ ] (for example: gain reported with uncertainty, in pC and electrons)
- [ ] (for example: one plot, axes labelled with units, saved to `results/`)

## Out of scope
What not to do, even if it looks helpful.

## Deliverables
Files, where they go, and the handoff note (`templates/handoff-note.md`).
