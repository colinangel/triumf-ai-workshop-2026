# Lab 2 · Calibrate your trust (25 min)

**Goal:** find out, by trying it, when a model's answer holds up and when it does not.
You will use what you see here all workshop to decide what needs checking.

Work in pairs and pick one track. Before each part, tell your partner what you expect
to happen. Afterwards, note what differed between the answers.

| Track | Parts | Where |
|-------|-------|-------|
| Beginner | A and C | the Claude app (chat) |
| Intermediate | B and D | Claude Code, or a terminal |
| Advanced | your own scenario | Claude Code |

## Beginner

### A. Same question, five times
Open five new chats. In each, ask exactly:

> In two sentences, what limits the timing resolution of a SiPM coupled to a fast scintillator?

Compare the five answers. What stayed the same, what changed, and does the change matter?

### C. A citation you can check
A reference the model produces from memory can be invented or attached to the wrong paper.
One it finds with search can be real but still not say what the answer claims. Either way,
you only know by opening it.

1. **Web search off** (in the chat's tools menu). Ask: *"Give me the full reference (authors, journal, year, DOI) for a paper that measured optical crosstalk in Hamamatsu MPPCs."*
   Open the DOI. Does the paper exist? Is it the paper described? Does it say what the answer claimed?
2. **Web search on**, in a new chat, same question. Open the source and ask the same three questions.

## Intermediate

### B. The same calculation, in the model and in code
Converting a pulse integral to charge is a chain of small steps: ADC counts to millivolts,
samples to nanoseconds, the 50-ohm input, the preamplifier, then pC to electrons. Current models
usually get it right. The question is how often they don't, and whether you could tell.

1. **Run the trial**, in a terminal:

   ```
   uv run python labs/day1/lab2-trust/arith_trial.py
   ```

   or ask Claude Code: *"Run `uv run python labs/day1/lab2-trust/arith_trial.py` and explain the table."*
   It asks Sonnet the same question 10 times at low reasoning effort and 10 at high, with every
   tool switched off. Each answer prints as it comes back, marked right or WRONG against the kit's
   own conversion, then a tally. About 40 seconds.
2. **Look at the wrong answers.** How far off are they? Rerun with `--show-working` to read each
   wrong answer's full working. Could you have spotted the mistake from the working alone?
3. **Try Opus** with `--model opus`. Fewer mistakes at low effort, or none? At what cost per answer?

The correct answer is the first line of the output, computed by one line of Python in a few microseconds.

### D. Deterministic tool, stochastic driver
In Claude Code: *"Run `uv run wfkit info data/sipm_lowlight.parquet` and tell me the sample period and preamplifier gain."*
Run it twice in fresh sessions. The numbers come from a tool, so they should not change. Did the wording around them?

## Advanced: your own scenario
Pick a calculation or factual question from your own work whose answer you can compute or look up
independently: a unit conversion, a rate, a resolution, a physical constant, a cross-section.

1. Copy the part B script: `cp labs/day1/lab2-trust/arith_trial.py work/my_trial.py`
2. Ask Claude Code to change `work/my_trial.py` for your question: the prompt (keep "Without using
   any tools" and a fixed `ANSWER:` line), the true value, and `score()` with a tolerance you can defend.
3. Run it: `uv run python work/my_trial.py`, then again with `--model opus`.

Does your own work hit the same failure? And what did writing the scorer force you to pin down? If
you could not say what counts as a right answer, that is the finding: an answer you cannot score is
one you cannot check.

## Done when
You can say what differed between the answers you got, which of them you would have trusted
without checking, and one rule for what you will always check yourself from now on, for example
"every reference I open before I cite it, and every number the model worked out without code".
