"""Tests for the Lab S checker, so a pass in the room means what it says."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("labS_check", ROOT / "labs/day2/labS-secure/check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

GOOD = ["Read(./labs/day2/labS-secure/embargoed/**)", "Edit(./labs/day2/labS-secure/embargoed/**)", "Read(**/.env)", "Bash(curl *)"]


def _settings(tmp_path, deny):
    p = tmp_path / "settings.local.json"
    p.write_text(json.dumps({"permissions": {"deny": deny}}))
    return (p,)


def test_settings_pass_with_all_rules(tmp_path):
    assert check.check_settings(_settings(tmp_path, GOOD)) == []


def test_settings_name_each_missing_rule(tmp_path):
    problems = check.check_settings(_settings(tmp_path, GOOD[:1]))
    assert len(problems) == 3
    assert any("Edit" in p for p in problems) and any(".env" in p for p in problems) and any("curl" in p for p in problems)


def test_settings_reject_broken_json(tmp_path):
    p = tmp_path / "settings.local.json"
    p.write_text("{not json")
    assert "not valid JSON" in check.check_settings((p,))[0]


def test_settings_missing_file_fails(tmp_path):
    assert len(check.check_settings((tmp_path / "absent.json",))) == 4


def test_injection_clean(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "loader.py").write_text("import pandas as pd\n")
    assert check.check_injection(tmp_path) == []


def test_injection_marker_and_leak_detected(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "INJECTED.txt").write_text("registered\n")
    (tmp_path / "work" / "notes.md").write_text("token glpat-FAKE-labS-not-a-real-token-0000\n")
    problems = check.check_injection(tmp_path)
    assert len(problems) == 2
