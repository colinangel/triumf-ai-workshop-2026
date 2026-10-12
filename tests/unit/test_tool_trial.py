"""Tests for the Lab 2 tool trial: numbers that come from a tool, asked 20 times."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("tool_trial", ROOT / "labs/day1/lab2-trust/tool_trial.py")
trial = importlib.util.module_from_spec(spec)
sys.modules["tool_trial"] = trial
spec.loader.exec_module(trial)


def test_truth_comes_from_the_run_metadata():
    assert trial.TRUE_DT_NS == 4.0 and trial.TRUE_GAIN == 30.0


def test_prompt_names_the_tool_and_the_answer_format():
    assert "uv run wfkit info data/sipm_lowlight.parquet" in trial.PROMPT
    assert "ANSWER:" in trial.PROMPT


@pytest.mark.parametrize(
    "line, ok",
    [
        ("ANSWER: 4.0 ns, gain 30", True),
        ("ANSWER: 4 ns, gain 30.0", True),
        ("ANSWER: 4.0 ns, gain 30x", True),
        ("ANSWER: 2.0 ns, gain 30", False),
        ("ANSWER: 4.0 ns, gain 3", False),
    ],
)
def test_score(line, ok):
    s = trial.score(f"The tool says...\n{line}")
    assert s.parsed and s.correct is ok


def test_unparsed_is_not_correct():
    s = trial.score("sample period is four nanoseconds")
    assert not s.parsed and not s.correct


def test_distinct_wordings_ignores_whitespace():
    assert trial.distinct(["a  b\n", "a b", "c"]) == 2


def test_live_line_shows_tool_use_and_verdict():
    r = {"effort": "low", "seconds": 7.0, "answer": "4.0 ns, gain 30", "parsed": True, "correct": True, "tool_calls": 1}
    line = trial.live_line(2, r)
    assert "right" in line and "1 tool call" in line and "#2" in line
    r2 = {**r, "correct": False, "answer": "2.0 ns, gain 30", "tool_calls": 0}
    assert "WRONG" in trial.live_line(3, r2) and "no tool call" in trial.live_line(3, r2)
