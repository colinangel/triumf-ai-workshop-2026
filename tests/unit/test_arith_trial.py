"""Tests for the Lab 2 part B trial script: the scoring must call real answers right and wrong."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("arith_trial", ROOT / "labs/day1/lab2-trust/arith_trial.py")
trial = importlib.util.module_from_spec(spec)
sys.modules["arith_trial"] = trial
spec.loader.exec_module(trial)


def test_truth_matches_kit_conversion():
    from wfkit.config import PRESETS

    assert trial.TRUE_PC == pytest.approx(1853 * PRESETS["sipm_lowlight"].adc_samples_to_pc, rel=1e-12)
    assert trial.TRUE_PC == pytest.approx(0.60319, rel=1e-4)
    assert trial.TRUE_ELECTRONS == pytest.approx(3.7648e6, rel=1e-4)


def test_prompt_states_the_metadata_and_the_answer_format():
    p = trial.PROMPT
    for text in ("0.1220703125", '"dt_ns": 4.0', '"impedance_ohm": 50.0', '"preamp_gain": 30.0', "1853", "ANSWER:"):
        assert text in p
    assert "Without using any tools" in p


# Answer lines recorded from real runs on 12 October 2026.
@pytest.mark.parametrize(
    "line, factor",
    [
        ("ANSWER: 0.603 pC, 3.76e6 electrons", 1.0),
        ("ANSWER: 0.6032 pC, 3,764,817 electrons", 1.0),
        ("ANSWER: 0.603 pC, 3.765 × 10⁶ electrons", 1.0),
        ("ANSWER: 0.00603 pC, 37650 electrons", 0.01),
        ("ANSWER: 6.03e-4 pC, 3765 electrons", 0.001),
        ("ANSWER: 2.41 pC, 1.51e7 electrons", 4.0),
        ("ANSWER: 6.03 × 10⁻⁴ pC, 3.76 × 10³ electrons", 0.001),
    ],
)
def test_parse_and_score_recorded_answers(line, factor):
    result = trial.score(f"some working...\n{line}")
    assert result.parsed
    assert result.factor == pytest.approx(factor, rel=0.01)
    assert result.correct is (factor == 1.0)


def test_last_answer_line_wins():
    assert trial.score("ANSWER: 0.006 pC, 3.7e4 electrons\nrechecked\nANSWER: 0.6032 pC, 3.76e6 electrons").correct


def test_missing_answer_is_not_counted_correct():
    r = trial.score("I think it is about 0.6 pC.")
    assert not r.parsed and not r.correct


def test_electron_count_must_agree_too():
    # right charge, wrong electrons: still wrong
    r = trial.score("ANSWER: 0.6032 pC, 37650 electrons")
    assert r.parsed and not r.correct


def _result(effort="low", **kw):
    base = {"effort": effort, "seconds": 6.2, "cost_usd": 0.008, "tool_turns": 0, "answer": "", "reply": ""}
    return {**base, **kw}


def test_live_line_for_a_right_answer():
    line = trial.live_line(3, _result(answer="0.6032 pC, 3.765e6 electrons", parsed=True, correct=True, factor=1.0))
    assert "right" in line and "0.6032 pC" in line and "low" in line and "#3" in line and "6 s" in line


def test_live_line_for_a_wrong_answer_names_the_factor():
    line = trial.live_line(7, _result(effort="high", answer="0.00603 pC, 37650 electrons", parsed=True, correct=False, factor=0.01))
    assert "WRONG" in line and "x0.01" in line and "high" in line


def test_live_line_for_a_missing_answer_and_an_error():
    assert "no ANSWER line" in trial.live_line(1, _result(parsed=False, correct=False))
    assert "failed" in trial.live_line(2, {"effort": "low", "error": "TimeoutExpired"})
