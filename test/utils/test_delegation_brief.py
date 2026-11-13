"""Tests for the delegation brief guard (utils/delegation_brief.py)."""

from cli_agent_orchestrator.utils.delegation_brief import (
    MAX_BRIEF_CHARS,
    check_delegation_brief,
)


def test_short_brief_with_pointer_is_accepted():
    msg = "Review the diff in worktree ../wt-api and report bugs. Notes: docs/review.md"
    assert check_delegation_brief(msg) is None


def test_message_over_limit_is_refused():
    reason = check_delegation_brief("x" * (MAX_BRIEF_CHARS + 1))
    assert reason is not None and "limit" in reason


def test_message_at_limit_is_accepted():
    assert check_delegation_brief("x" * MAX_BRIEF_CHARS) is None


def test_pasted_transcript_is_refused():
    transcript = "User: fix the bug\nAssistant: sure, here is the fix\nUser: thanks"
    reason = check_delegation_brief(transcript)
    assert reason is not None and "transcript" in reason


def test_two_speaker_lines_are_still_a_brief():
    assert check_delegation_brief("User: see issue 12\nAssistant asks: keep it short") is None
