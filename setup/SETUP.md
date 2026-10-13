# Setup: do this by Wednesday 14 October

Allow 20 minutes, more on a Mac that needs Apple's command line tools (step 1). If anything fails,
send the output of the step that failed to the workshop organiser before the day, so it can be
fixed in advance.

Supported: macOS, Linux, and Windows through WSL 2 (recommended) or native PowerShell.

This page installs git, uv and Claude Code, plus optional C++ tools. You clone the workshop kit
itself in Lab 1, at the start of Day 1.

## 1. Git
Check `git --version`. If it is missing:

- macOS: `xcode-select --install` (on a fresh Mac, `git --version` offers the same installer).
  This installs Apple's command line tools, git included. It is about a 1 GB download, so start
  it early and let it finish before step 2.
- Ubuntu/WSL: `sudo apt install git`
- Windows: https://git-scm.com

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

## 4. Where you will work
Pick one; every lab works in all three, and they share your sign-in and the kit's project settings.

- **The Claude desktop app** (https://claude.ai/download), Code tab. The app is also used on
  Day 2 for the research module, so install it either way.
- **VS Code**, with the Claude Code extension from the VS Code marketplace. It shows diffs inline.
- **A terminal**, running `claude` in the kit folder.

## 5. Check
In a terminal:

```
git --version
uv --version
claude -p "Reply with the word ready"
```

The first two print version numbers. The last should print `ready`: that confirms Claude Code is
installed and signed in to your TRIUMF account. If it prints anything else, send the output to the
workshop organiser.

## 6. Optional, for the C++ challenges
CMake 3.20 or later and a C++20 compiler (GCC 11+, Clang 14+, or Xcode command line tools).
macOS: the command line tools from step 1, then `brew install cmake` (or the installer from https://cmake.org/download). Ubuntu/WSL: `sudo apt install build-essential cmake`. Windows: use WSL 2 for these.
Check with `cmake --version`.

## Editor
Any editor works for reading and editing the kit.
