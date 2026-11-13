"""Tests for the needs-you flag store (utils/needs_you.py)."""

from cli_agent_orchestrator.utils.needs_you import (
    clear_flag,
    handle_payload,
    list_flags,
    set_flag,
)


def test_set_then_list_then_clear(tmp_path):
    set_flag("s1", "permission prompt", tmp_path)
    flags = list_flags(tmp_path)
    assert [f["session"] for f in flags] == ["s1"]
    assert flags[0]["reason"] == "permission prompt"
    clear_flag("s1", tmp_path)
    assert list_flags(tmp_path) == []


def test_clear_missing_flag_is_noop(tmp_path):
    clear_flag("never-set", tmp_path)  # must not raise


def test_claude_notification_sets_flag(tmp_path):
    payload = {"hook_event_name": "Notification", "session_id": "c1", "message": "Needs permission"}
    assert handle_payload(payload, tmp_path) is True
    assert list_flags(tmp_path)[0]["reason"] == "Needs permission"


def test_claude_stop_sets_flag_and_prompt_clears(tmp_path):
    handle_payload({"hook_event_name": "Stop", "session_id": "c2"}, tmp_path)
    assert len(list_flags(tmp_path)) == 1
    handle_payload({"hook_event_name": "UserPromptSubmit", "session_id": "c2"}, tmp_path)
    assert list_flags(tmp_path) == []


def test_codex_turn_complete_sets_flag(tmp_path):
    payload = {"type": "agent-turn-complete", "thread-id": "x1"}
    assert handle_payload(payload, tmp_path) is True
    assert list_flags(tmp_path)[0]["session"] == "x1"


def test_unknown_or_sessionless_payloads_are_ignored(tmp_path):
    assert handle_payload({"hook_event_name": "PreToolUse", "session_id": "c3"}, tmp_path) is False
    assert handle_payload({"hook_event_name": "Stop"}, tmp_path) is False
    assert handle_payload({"type": "other"}, tmp_path) is False
    assert list_flags(tmp_path) == []


def test_half_written_file_is_skipped(tmp_path):
    (tmp_path / "bad.json").write_text("{not json")
    set_flag("good", "ok", tmp_path)
    assert [f["session"] for f in list_flags(tmp_path)] == ["good"]
