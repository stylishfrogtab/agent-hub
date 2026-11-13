"""A corrupt alert-state file must fail the check, not get overwritten (GH #737 pattern)."""

import pytest

from cli_agent_orchestrator.utils.usage_monitor import check, save_status_line


def test_corrupt_state_file_raises_and_is_not_overwritten(tmp_path):
    usage = tmp_path / "usage.json"
    state = tmp_path / "state.json"
    save_status_line({"rate_limits": {"five_hour": {"used_percentage": 85}}}, usage)
    state.write_text("{not json")
    with pytest.raises(ValueError):
        check(state, usage)
    assert state.read_text() == "{not json"
