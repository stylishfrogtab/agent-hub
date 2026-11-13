"""Tests for the Claude usage alert logic (utils/usage_monitor.py)."""

from cli_agent_orchestrator.utils.usage_monitor import (
    check,
    due_alerts,
    extract,
    read_usage,
    save_status_line,
)


def test_extract_reads_both_windows():
    payload = {
        "rate_limits": {"five_hour": {"used_percentage": 42}, "seven_day": {"used_percentage": 7.5}}
    }
    assert extract(payload) == {"five_hour": 42.0, "seven_day": 7.5}


def test_extract_tolerates_missing_fields():
    assert extract({}) == {"five_hour": None, "seven_day": None}
    assert extract({"rate_limits": {"five_hour": {}}}) == {"five_hour": None, "seven_day": None}
    assert extract({"rate_limits": "garbage"}) == {"five_hour": None, "seven_day": None}


def test_non_numeric_percentage_is_ignored():
    assert extract({"rate_limits": {"five_hour": {"used_percentage": "80"}}})["five_hour"] is None
    assert extract({"rate_limits": {"five_hour": {"used_percentage": True}}})["five_hour"] is None


def test_missing_usage_file_reads_as_none(tmp_path):
    assert read_usage(tmp_path / "nope.json") == {"five_hour": None, "seven_day": None}


def test_alerts_fire_once_per_threshold():
    sent: list = []
    assert due_alerts("five_hour", 50, sent) == []
    assert due_alerts("five_hour", 81, sent) == [80]
    assert due_alerts("five_hour", 82, sent) == []
    assert due_alerts("five_hour", 96, sent) == [95]
    assert due_alerts("five_hour", 99, sent) == []


def test_jump_past_both_thresholds_fires_both():
    assert due_alerts("seven_day", 97, []) == [80, 95]


def test_drop_below_80_rearms_alerts():
    sent: list = []
    due_alerts("five_hour", 85, sent)
    due_alerts("five_hour", 10, sent)
    assert due_alerts("five_hour", 85, sent) == [80]


def test_missing_value_never_alerts():
    assert due_alerts("five_hour", None, []) == []


def test_check_records_state_so_alerts_do_not_repeat(tmp_path):
    usage = tmp_path / "usage.json"
    state = tmp_path / "state.json"
    save_status_line({"rate_limits": {"five_hour": {"used_percentage": 85}}}, usage)
    first = check(state, usage)
    assert first == ["Claude five hour usage at 85% (over 80%)"]
    assert check(state, usage) == []
