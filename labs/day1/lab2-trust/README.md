# Lab 2 · Calibrate your trust (25 min)

**Goal:** predict, then measure, when a model's answer is stable and when it is not.
You will use the results all workshop to decide what needs checking.

Work in pairs. Use the Claude app (chat) for parts A and C, and Claude Code or a terminal for parts B and D.
Record predictions in `worksheet.md` **before** you run anything.

## A. Same question, five times
Open five new chats. In each, ask exactly:

> In two sentences, what limits the timing resolution of a SiPM coupled to a fast scintillator?

Compare the five answers. What stayed the same, what changed, and does the change matter?

## B. The same calculation, in the model and in code
Converting a pulse integral to charge is a chain of small steps: ADC counts to millivolts,
samples to nanoseconds, the 50-ohm input, the preamplifier, then pC to electrons. Current models
usually get it right. The question is how often they don't, and whether you could tell.

1. **Predict** on the worksheet: out of 10 tries, how many wrong answers at low reasoning effort,
   and how many at high?
2. **Run the trial.** Either in a terminal:

   ```
   uv run python labs/day1/lab2-trust/arith_trial.py
   ```

   or ask Claude Code: *"Run `uv run python labs/day1/lab2-trust/arith_trial.py` and explain the table."*
   It asks Sonnet the same question 10 times at low effort and 10 at high, with every tool switched
   off, and prints each answer as it comes back, marked right or WRONG against the kit's own
   conversion, then a tally. About 40 seconds.
3. **Look at the wrong answers.** How far off are they? Rerun with `--show-working` to read each wrong
   answer's full working. Could you have spotted the mistake from the working alone?
4. **Add your row** to the room's results sheet: right and wrong at low and at high.

The correct answer is in the table's first line, computed by one line of Python in a few microseconds.

## C. A citation you can check
The point: a reference the model produces from memory can be invented or misattributed, and one
it finds with search can be real but still not say what the answer claims. Either way, you only
know by opening it.

1. **Web search off** (in the chat's tools menu). Ask: *"Give me the full reference (authors, journal, year, DOI) for a paper that measured optical crosstalk in Hamamatsu MPPCs."*
   Open the DOI. Does the paper exist? Is it the paper described? Does it say what the answer claimed?
2. **Web search on**, in a new chat, same question. Open the source again and answer the same three questions.

Record both on the worksheet (C1 and C2).

## D. Deterministic tool, stochastic driver
In Claude Code: *"Run `uv run wfkit info data/sipm_lowlight.parquet` and tell me the sample period and preamplifier gain."*
Run it twice in fresh sessions. The numbers come from a tool, so they should not change. Did the wording around them?

## Tiers
- **Beginner:** do A to D as written.
- **Intermediate:** in A, change one word of the prompt ("fast" to "slow") and see whether the answer tracks the physics or the phrasing.
- **Advanced:** rerun B with `--model haiku --n 5` and `--model opus --n 5`. Is the more expensive model more reliable, or only more expensive? Then in A, run `claude -p "<prompt A>" --output-format json` five times with `--model haiku` and then `--model opus`. Compare cost (`total_cost_usd`) and answer spread. Is the more expensive model more consistent, more correct, or both?

## Acceptance
Your worksheet has a prediction and an observed result for each part, and one
sentence on what you will verify by default from now on.

## Debrief question
Which of A to D would you have trusted without checking, and were you right to?
