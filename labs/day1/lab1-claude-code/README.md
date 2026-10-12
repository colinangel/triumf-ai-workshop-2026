# Lab 1 · Claude Code onboarding (30 min)

**Goal:** a working Claude Code session in this repository, and the controls you
will use for the rest of the workshop: model, effort, permission mode, plan mode,
and how to see what the session is costing.

If `uv run python setup/check_setup.py` passed before the workshop, start at step 2.

## 1. Install and sign in
Follow `setup/SETUP.md`. Sign in with your TRIUMF Claude Enterprise account. Check:

```
claude --version
claude doctor
```

## 2. First session
From the repository root:

```
claude
```

Ask: *"Explain what this repository is for and how its pieces fit together. Cite file paths."*
Then check two of the paths it gave you actually say what it claims.

## 3. Controls to try (type each in the session)

| Command | What it does | Try |
|---------|--------------|-----|
| `/model` | choose the model (aliases: `opus`, `sonnet`, `haiku`, `best`) | switch to `sonnet`, then back |
| `/effort` | how much reasoning per turn (`low` to `max`, or `auto`) | set `low`, ask a hard question, set `high`, ask again |
| Shift+Tab | cycle permission modes: Manual, accept edits, plan, auto | find plan mode |
| `/plan <task>` | start in plan mode: Claude proposes before touching files | `/plan add a --quiet flag to the wfkit CLI` |
| `/context` | what is filling the context window | look before and after reading a big file |
| `/usage` | session cost and plan usage | check after step 4 |
| `/memory` | open the CLAUDE.md files in effect | find this project's `CLAUDE.md` |

**Auto mode** runs actions without asking you each time. A separate classifier
model reviews each action and blocks anything that goes beyond your request,
touches infrastructure it does not recognise, or appears driven by content
Claude read (for example, instructions hidden in a downloaded file). Blocked
actions are listed under `/permissions`. It reduces prompts; it does not
remove your responsibility for what runs. Your organisation's administrators
can switch it off.

## 4. Plan, then approve
Using `/plan`, ask for the `--quiet` flag. Read the plan. Approve with
"manually approve edits" and accept each edit only if you understand it. Run
`uv run pytest` afterwards.

## Tiers
- **Beginner:** steps 1 to 4.
- **Intermediate:** repeat step 4 in auto mode. Note which actions ran without asking and which, if any, were blocked.
- **Advanced:** run the same request headless: `claude -p "..." --output-format json --permission-mode plan`. Read `total_cost_usd` and `usage` in the JSON. Then write a `.claude/settings.json` that allows `Bash(uv run pytest*)` without prompting, and explain in one line why you would not allow `Bash(*)`.

## Acceptance
`uv run pytest` passes after your change, and you can say which permission mode
you used and why.
