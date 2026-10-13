# Lab 2 · Calibrate your trust (25 min)

**Goal:** find out, by trying it, when a model's answer holds up and when it does not.
You will use what you see here all workshop to decide what needs checking.

Work in pairs and pick one track. The tracks run from easiest to hardest. Before each part, tell
your partner what you expect to happen. Afterwards, note what differed between the answers.

| Track | Parts | Where |
|-------|-------|-------|
| Beginner | A and B | the Claude app (chat) |
| Intermediate | C and D | Claude Code (any surface), or a terminal |
| Advanced | your own scenario | Claude Code (any surface) |

**Before you start:** Beginner: in the Claude app, choose **Sonnet** in the model picker. Intermediate and
Advanced: nothing to set; the scripts run Sonnet at low and at high effort themselves, and the
steps say when to add `--model opus`.

## Beginner

### A. Same question, five times
Open five new chats. In each, ask exactly:

> In two sentences, what limits the timing resolution of a SiPM coupled to a fast scintillator?

Compare the five answers. What stayed the same, what changed, and does the change matter?

### B. A citation you can check
A reference the model produces from memory can be invented or attached to the wrong paper.
One it finds with search can be real but still not say what the answer claims. Either way,
you only know by opening it.

1. **From memory.** Ask: *"Without using web search, give me the full reference (authors, journal, year) for a paper that measured optical crosstalk in Hamamatsu MPPCs."*
   Look the paper up yourself. Does it exist? Is it the paper described? Does it say what the answer claimed?
2. **With search.** In a new chat: *"Search the web and give me the full reference, with a link, for a paper that measured optical crosstalk in Hamamatsu MPPCs."*
   Open the link and ask the same three questions.

## Intermediate
C and D ask Sonnet the same kind of question 20 times each, 10 at low reasoning effort and 10 at
high. The only difference: in C the model works the number out itself, in D it reads it from a tool.
C shows the problem; D shows the fix. Run them in a terminal, or ask Claude in your Claude Code session to run each
one and explain the table. Each answer prints as it comes back, marked right or WRONG, then a tally.

### C. A calculation the model works out itself, 20 times
Converting a pulse integral to charge is a chain of small steps: ADC counts to millivolts,
samples to nanoseconds, the 50-ohm input, the preamplifier, then pC to electrons. Current models
usually get it right. The question is how often they don't, and whether you could tell.

```
uv run python labs/day1/lab2-trust/arith_trial.py
```

Every tool is switched off, so the model does the arithmetic itself. The correct answer is the first
line of the output, computed by one line of Python in a few microseconds. About 40 seconds.

1. **Look at the wrong answers.** How far off are they? Rerun with `--show-working` to read each
   wrong answer's full working. Could you have spotted the mistake from the working alone?
2. **Try Opus** with `--model opus`. Fewer mistakes at low effort, or none? At what cost per answer?

### D. Numbers from a tool, 20 times

```
uv run python labs/day1/lab2-trust/tool_trial.py
```

Claude runs `uv run wfkit info data/sipm_lowlight.parquet` and reports the sample period and the
preamplifier gain; it may run that one command and nothing else. Same model, same settings, same
number of tries as C. Were the numbers ever wrong? How many different wordings did the 20 answers use?
Add `--show-replies` to read them all. About 40 seconds.

**Put D next to C.** What made the difference, and what does that tell you about where the numbers
in your own analysis should come from?

## Advanced: your own scenario
Pick a calculation or factual question from your own work whose answer you can compute or look up
independently: a unit conversion, a rate, a resolution, a physical constant, a cross-section.

1. Copy the part C script: `cp labs/day1/lab2-trust/arith_trial.py work/my_trial.py`
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
