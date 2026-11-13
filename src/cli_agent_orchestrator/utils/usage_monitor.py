"""Claude Code usage alerts at 80% and 95% of the five-hour and seven-day windows.

A Claude Code status-line hook passes a JSON payload on stdin. ``save_status_line``
copies its ``rate_limits`` percentages to one small file. ``check`` reads that file,
returns the alerts that are due, and remembers them so each one fires once per window.

Field names (``rate_limits.five_hour.used_percentage`` and
``rate_limits.seven_day.used_percentage``) come from the owner's brief and are not
verified on the owner's Mac. Any field may be missing; a missing value never alerts.

shortcut: alerts are deduped in a JSON state file; no file locking.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

USAGE_FILE_ENV = "AGENT_HUB_USAGE_FILE"
THRESHOLDS = (80, 95)
WINDOWS = ("five_hour", "seven_day")


def usage_file() -> Path:
    return Path(os.environ.get(USAGE_FILE_ENV, Path.home() / ".agent-hub" / "claude-usage.json"))


def _percent(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def extract(payload: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Pull the window percentages out of a status-line payload. Missing values are None."""
    limits = payload.get("rate_limits") if isinstance(payload, dict) else None
    limits = limits if isinstance(limits, dict) else {}
    result: Dict[str, Optional[float]] = {}
    for window in WINDOWS:
        entry = limits.get(window)
        entry = entry if isinstance(entry, dict) else {}
        result[window] = _percent(entry.get("used_percentage"))
    return result


def save_status_line(payload: Dict[str, Any], path: Optional[Path] = None) -> None:
    path = path or usage_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(extract(payload)))


def read_usage(path: Optional[Path] = None) -> Dict[str, Optional[float]]:
    """Latest saved percentages. An absent or unreadable file gives all None."""
    path = path or usage_file()
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {w: None for w in WINDOWS}
    return {w: _percent(data.get(w)) for w in WINDOWS}


def due_alerts(window: str, percent: Optional[float], sent: List[int]) -> List[int]:
    """Thresholds newly crossed for one window. ``sent`` is updated in place.

    Dropping back below 80 clears the window's sent alerts, so the next climb alerts again.
    """
    if percent is None:
        return []
    if percent < THRESHOLDS[0]:
        sent.clear()
        return []
    due = [t for t in THRESHOLDS if percent >= t and t not in sent]
    sent.extend(due)
    return due


def check(state_path: Optional[Path] = None, path: Optional[Path] = None) -> List[str]:
    """Return alert messages due now, and record them in the state file."""
    state_path = state_path or usage_file().with_name("usage-alerts-sent.json")
    try:
        sent_all = json.loads(state_path.read_text())
    except (OSError, ValueError):
        sent_all = {}
    messages: List[str] = []
    for window, percent in read_usage(path).items():
        sent = list(sent_all.get(window, []))
        for threshold in due_alerts(window, percent, sent):
            messages.append(
                f"Claude {window.replace('_', ' ')} usage at {percent:.0f}% (over {threshold}%)"
            )
        sent_all[window] = sent
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(sent_all))
    return messages


def notify_macos(title: str, message: str) -> None:
    """Show a macOS notification. Arguments are passed as argv, never through a shell."""
    script = (
        "on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run"
    )
    subprocess.run(["osascript", "-e", script, title, message], check=False)


def main(argv: List[str]) -> int:
    if len(argv) > 1 and argv[1] == "save":
        try:
            save_status_line(json.load(sys.stdin))
        except ValueError:
            pass  # a status-line hook must never break the status line
        return 0
    for message in check():
        notify_macos("agent-hub", message)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
