# Setup: do this before 16 October

Allow 20 minutes. If anything fails, send the output of the last step to the
workshop organiser before the day, so it can be fixed in advance.

Supported: macOS, Linux, and Windows through WSL 2 (recommended) or native PowerShell.

## 1. Git
Check `git --version`. If missing: macOS `xcode-select --install`; Ubuntu/WSL `sudo apt install git`; Windows https://git-scm.com.

## 2. uv (Python and packages)
uv installs the right Python and every package; you do not need an existing Python.

- macOS, Linux, WSL: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Open a new terminal, then `uv --version`.

## 3. Claude Code
- macOS, Linux, WSL: `curl -fsSL https://claude.ai/install.sh | bash`
- Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
- Or with a package manager: `brew install --cask claude-code` (macOS), `winget install Anthropic.ClaudeCode` (Windows)

On a shared cluster or a network home directory, install to local disk, not shared storage.

Install this even if you will work in the desktop app or VS Code: some lab scripts call
`claude` from the command line, and neither the app nor the extension installs it.

Then run `claude` once in a terminal, choose to sign in with your Claude account, and use your
**TRIUMF Claude Enterprise** login. Type `/exit` to leave. Check with `claude doctor`.

## 3b. Where you will work
Pick one; every lab works in all three, and they share your sign-in and the kit's project settings.

- **The Claude desktop app** (https://claude.ai/download), Code tab. The app is also used on
  Day 2 for the research module, so install it either way.
- **VS Code**, with the Claude Code extension from the VS Code marketplace. It shows diffs inline.
- **A terminal**, running `claude` in the kit folder.

## 4. The workshop kit

```
git clone https://github.com/colinangel/triumf-ai-workshop-2026.git
cd triumf-ai-workshop-2026
uv sync
uv run wfkit generate --all
uv run python setup/check_setup.py
```

Every line of the last command should read PASS or WARN.

If the kit changes before the workshop you will be told; update with `git pull` in the kit folder.

## 5. Optional, for the C++ challenges
CMake 3.20 or later and a C++20 compiler (GCC 11+, Clang 14+, or Xcode command line tools).
macOS: `xcode-select --install` and `brew install cmake`. Ubuntu/WSL: `sudo apt install build-essential cmake`.

## Editor
Any editor works for reading and editing the kit.
