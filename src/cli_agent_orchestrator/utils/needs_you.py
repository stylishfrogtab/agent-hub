"""Per-session "needs you" flags written by agent hooks and read by the dashboard.

One JSON file per session in a flag directory. A hook sets the flag when an agent
waits for the owner (permission prompt, idle after a turn) and clears it when the
owner sends input again.

Hook entry point: ``python -m cli_agent_orchestrator.utils.needs_you`` reads one
JSON payload on stdin (Claude Code hooks) or from argv[1] (Codex ``notify``).
The field names below are assumptions to verify on the owner's Mac.

shortcut: no file locking; one writer per session, last write wins.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

FLAG_DIR_ENV = "AGENT_HUB_FLAG_DIR"
_SET_EVENTS = {"Notification", "Stop"}
_CLEAR_EVENTS = {"UserPromptSubmit"}
_CODEX_SET_TYPES = {"agent-turn-complete"}


def flag_dir() -> Path:
    return Path(os.environ.get(FLAG_DIR_ENV, Path.home() / ".agent-hub" / "needs-you"))


def _flag_path(session: str, directory: Path) -> Path:
    return directory / f"{session}.json"


def set_flag(session: str, reason: str, directory: Optional[Path] = None) -> None:
    directory = directory or flag_dir()
    directory.mkdir(parents=True, exist_ok=True)
    record = {"session": session, "reason": reason, "since": datetime.now(timezone.utc).isoformat()}
    _flag_path(session, directory).write_text(json.dumps(record))


def clear_flag(session: str, directory: Optional[Path] = None) -> None:
    directory = directory or flag_dir()
    _flag_path(session, directory).unlink(missing_ok=True)


def list_flags(directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    directory = directory or flag_dir()
    if not directory.is_dir():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        try:
            records.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            continue  # a half-written file is skipped, not fatal
    return records


def handle_payload(payload: Dict[str, Any], directory: Optional[Path] = None) -> bool:
    """Apply one hook payload. Returns True when a flag was set or cleared."""
    if "hook_event_name" in payload:  # Claude Code hook
        session = payload.get("session_id")
        event = payload.get("hook_event_name")
        if not session:
            return False
        if event in _SET_EVENTS:
            set_flag(session, str(payload.get("message") or event), directory)
            return True
        if event in _CLEAR_EVENTS:
            clear_flag(session, directory)
            return True
        return False
    if payload.get("type") in _CODEX_SET_TYPES:  # Codex notify
        session = payload.get("thread-id")
        if not session:
            return False
        set_flag(session, "codex turn complete", directory)
        return True
    return False


def main(argv: List[str]) -> int:
    raw = argv[1] if len(argv) > 1 else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except ValueError:
        return 0  # a hook must never block the agent on bad input
    handle_payload(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
