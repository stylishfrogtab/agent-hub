"""Tests for the delegated-work approval store (utils/approval_gate_local.py)."""

import pytest

from cli_agent_orchestrator.utils.approval_gate_local import (
    APPROVED,
    DENIED,
    PENDING,
    decide,
    is_approved,
    list_pending,
    read,
    request,
)


def test_new_request_is_pending_and_not_approved(tmp_path):
    request("r1", "edit src/x.py", tmp_path)
    assert read("r1", tmp_path)["status"] == PENDING
    assert is_approved("r1", tmp_path) is False
    assert [r["id"] for r in list_pending(tmp_path)] == ["r1"]


def test_owner_approval_allows_work(tmp_path):
    request("r1", "run tests", tmp_path)
    decide("r1", APPROVED, tmp_path)
    assert is_approved("r1", tmp_path) is True
    assert list_pending(tmp_path) == []


def test_denial_blocks_work(tmp_path):
    request("r1", "rm -rf build", tmp_path)
    decide("r1", DENIED, tmp_path)
    assert is_approved("r1", tmp_path) is False


def test_decision_is_final(tmp_path):
    request("r1", "x", tmp_path)
    decide("r1", APPROVED, tmp_path)
    with pytest.raises(ValueError):
        decide("r1", DENIED, tmp_path)


def test_unknown_decision_is_refused(tmp_path):
    request("r1", "x", tmp_path)
    with pytest.raises(ValueError):
        decide("r1", "maybe", tmp_path)


def test_request_cannot_overwrite_existing(tmp_path):
    request("r1", "x", tmp_path)
    with pytest.raises(FileExistsError):
        request("r1", "y", tmp_path)


def test_missing_request_fails_closed(tmp_path):
    assert is_approved("nope", tmp_path) is False
