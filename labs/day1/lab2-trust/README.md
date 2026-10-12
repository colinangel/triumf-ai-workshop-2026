# Lab 2 · Calibrate your trust (25 min)

**Goal:** predict, then measure, when a model's answer is stable and when it is not.
You will use the results all workshop to decide what needs checking.

Work in pairs. Use the Claude app (chat) for parts A to C and Claude Code for part D.
Record predictions in `worksheet.md` **before** you run anything.

## A. Same question, five times
Open five new chats. In each, ask exactly:

> In two sentences, what limits the timing resolution of a SiPM coupled to a fast scintillator?

Compare the five answers. What stayed the same, what changed, and does the change matter?

## B. Arithmetic in the model versus in code
In a new chat ask: *"Without using any tools, multiply 7,384,129 by 4,906,557. Give only the number."*
Then ask Claude Code, in this repository, to compute the same product with Python and show the command.
Check the answer with `uv run python -c "print(7384129*4906557)"`.

## C. A citation you can check
Ask: *"Give me the full reference (authors, journal, year, DOI) for a paper that measured optical crosstalk in Hamamatsu MPPCs."*
Open the DOI. Does the paper exist? Does it say what the answer claimed?
Repeat with web search switched on in the chat. Compare.

## D. Deterministic tool, stochastic driver
In Claude Code: *"Run `uv run wfkit info data/sipm_lowlight.parquet` and tell me the sample period and preamplifier gain."*
Run it twice in fresh sessions. The numbers come from a tool, so they should not change. Did the wording around them?

## Tiers
- **Beginner:** do A to D as written.
- **Intermediate:** in A, change one word of the prompt ("fast" to "slow") and see whether the answer tracks the physics or the phrasing.
- **Advanced:** in Claude Code, run `claude -p "<prompt A>" --output-format json` five times with `--model haiku` and then `--model opus`. Compare cost (`total_cost_usd`) and answer spread. Is the more expensive model more consistent, more correct, or both?

## Acceptance
Your worksheet has a prediction and an observed result for each part, and one
sentence on what you will verify by default from now on.

## Debrief question
Which of A to D would you have trusted without checking, and were you right to?
