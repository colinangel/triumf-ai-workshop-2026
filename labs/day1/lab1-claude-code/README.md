# Lab 1 · Claude Code onboarding (30 min)

**Goal:** a working Claude Code session in this repository, and the controls you
will use for the rest of the workshop: model, effort, permission mode, plan mode,
and how to see what the session is costing.

If `uv run python setup/check_setup.py` passed before the workshop, start at step 2.

**Before you start:** this lab uses **Sonnet at medium effort**; step 2 sets it.
Step 3 has you try other models and effort levels: switch back to Sonnet at medium when you are done.

## 1. Install and sign in
Follow `setup/SETUP.md` and sign in with your TRIUMF Claude Enterprise account.

Work in whichever surface you prefer: the Code tab of the Claude desktop app, the Claude Code
extension in VS Code, or a terminal. The labs name each setting; the table in step 3 shows where
to find it in yours. Some lab scripts call the command-line `claude` themselves, so it must be
installed whichever surface you use: `uv run python setup/check_setup.py` checks it.

## 2. First session
Open a session in the repository root:

- **Desktop app:** Code tab, **+ New session**, choose the kit folder.
- **VS Code:** open the kit folder, then the Claude Code panel.
- **Terminal:** `cd` into the kit folder and run `claude`.

Set the model to **Sonnet** and effort to **medium** (step 3 shows where).
Ask: *"Explain what this repository is for and how its pieces fit together. Cite file paths."*
Then check two of the paths it gave you actually say what it claims.

## 3. Controls to try

| Setting | Desktop app (Code tab) | VS Code | Terminal | Try |
|---------|------------------------|---------|----------|-----|
| Model | model menu next to the send button | the model name under the prompt box | `/model sonnet` | switch to Opus, then back to Sonnet |
| Effort | effort menu: Cmd+Shift+E (Windows: Ctrl+Shift+E) | Effort row in the model menu | `/effort medium` | set low, ask a hard question, set high, ask again, then back to medium |
| Permission mode | mode menu next to the send button | mode indicator under the prompt box | Shift+Tab cycles | find Manual, Accept edits, Plan and Auto |
| Plan mode | Plan in the mode menu | Plan in the mode menu | Shift+Tab to Plan | used in step 4 |
| New session | **+ New session** | a new conversation tab | `/clear` | used in later labs |

In any surface, type `/` in the prompt box to see the commands it offers. Look at `/context`
(what is filling the context window) before and after asking Claude to read a big file. Check
the session cost with `/usage`, or the usage ring next to the model menu in the desktop app.
Open `CLAUDE.md` in the repository root: every session here reads it first.

**Auto mode** runs actions without asking you each time. A separate classifier
model reviews each action and blocks anything that goes beyond your request,
touches infrastructure it does not recognise, or appears driven by content
Claude read (for example, instructions hidden in a downloaded file). The session
tells you when it blocks something. It reduces prompts; it does not remove your
responsibility for what runs. Your organisation's administrators can switch it off.

## 4. Plan, then approve: a small change to the kit's own tool
`wfkit` is the kit's command-line tool; setup used it to make the data. Run
`uv run wfkit generate --all` and look at the output: one line for every run it writes.
In a script or a batch job you want it silent unless something goes wrong. Your change:
a `--quiet` option that hides those lines and still prints errors.

1. Switch to Plan mode, so Claude reads and proposes but changes nothing yet.
2. Ask: *"Add a --quiet option to `wfkit generate` that hides the per-run lines but still
   prints errors. Include a test."*
3. Read the plan. Does it say which file it will change and how the test checks the output?
   Push back on anything vague before you approve.
4. Approve it with edits reviewed one at a time, and accept each edit only if you understand it.
5. Run `uv run pytest`, then `uv run wfkit generate --all --quiet`: it should print nothing.

## Tiers
- **Beginner:** steps 1 to 4.
- **Intermediate:** repeat step 4 in Auto mode, adding the same option to `wfkit export-wfb1`. Note which actions ran without asking and which, if any, were blocked.
- **Advanced:** run the same request headless, from a terminal (no app has an equivalent): `claude -p "..." --output-format json --permission-mode plan`. Read `total_cost_usd` and `usage` in the JSON. Then write a `.claude/settings.json` that allows `Bash(uv run pytest*)` without prompting, and explain in one line why you would not allow `Bash(*)`.

## Acceptance
`uv run pytest` passes after your change, `uv run wfkit generate --all --quiet` prints
nothing, and you can say which permission mode you used and why.
