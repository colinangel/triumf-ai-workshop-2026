# Build triage record

One file per build problem. Commit it next to the build files so the next
person finds it.

## Symptom
The first error message, verbatim, and the command that produced it.

## Environment
OS and version, compiler and version, CMake version, key dependency versions
(ROOT, Geant4, CUDA), container image and tag if any. Produce with commands, not memory:

```
uname -a; c++ --version; cmake --version; root-config --version; geant4-config --version; nvcc --version
```

## Hypotheses
| # | Hypothesis | Evidence for | Evidence against | Test |
|---|------------|--------------|------------------|------|

## What fixed it
The change, and why it works.

## Verification
A clean build from scratch (empty build directory, or a fresh container) succeeds.
Paste the last lines of that log.

## Pin it
Where the working versions are now recorded (container definition, `CMakePresets.json`,
environment module list) so the problem cannot come back silently.
