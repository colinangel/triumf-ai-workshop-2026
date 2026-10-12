"""Command-line options for the validation and challenge suites.

Each option overrides the matching environment variable, so the same commands
work in bash, zsh and Windows PowerShell:

    uv run pytest tests/validation --impl work.lab3:analyze
    uv run pytest tests/challenges --dark-impl work.c1:measure --timing-impl work.c2:measure
    uv run pytest tests/challenges --wfb1-reader build/cpp/wfb1_reader
    uv run pytest tests/security --wfb1-source work/reader
"""

import os

OPTIONS = {
    "--impl": "WFKIT_IMPL",
    "--dark-impl": "WFKIT_DARK",
    "--timing-impl": "WFKIT_TIMING",
    "--wfb1-reader": "WFB1_READER",
    "--wfb1-source": "WFB1_SOURCE",
}


def pytest_addoption(parser):
    group = parser.getgroup("wfkit", "workshop analysis under test")
    for flag, env in OPTIONS.items():
        group.addoption(flag, default=None, help=f"module:function or path (overrides ${env})")


def pytest_configure(config):
    for flag, env in OPTIONS.items():
        value = config.getoption(flag.lstrip("-").replace("-", "_"))
        if value:
            os.environ[env] = value
