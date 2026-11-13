"""Owner approval for delegated work that edits files or runs commands.

Each request is one JSON file in an approvals directory: ``pending``, ``approved``
or ``denied``. A worker that needs approval checks ``is_approved`` before it acts.
Only the owner sets ``approved`` or ``denied``, through ``decide``.

Not the same as ``services/approval_gate.py``, which gates scripted plan runs.

shortcut: no wiring into worker startup yet; this is the store and its rules only.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

APPROVALS_DIR_ENV = "AGENT_HUB_APPROVALS_DIR"
PENDING, APPROVED, DENIED = "pending", "approved", "denied"
_DECISIONS = {APPROVED, DENIED}


def approvals_dir() -> Path:
    return Path(os.environ.get(APPROVALS_DIR_ENV, Path.home() / ".agent-hub" / "approvals"))


def _path(request_id: str, directory: Path) -> Path:
    return directory / f"{request_id}.json"


def request(request_id: str, summary: str, directory: Optional[Path] = None) -> Dict[str, Any]:
    """Open a pending request. Refuses to overwrite an existing one."""
    directory = directory or approvals_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = _path(request_id, directory)
    if path.exists():
        raise FileExistsError(f"approval request {request_id} already exists")
    record = {
        "id": request_id,
        "summary": summary,
        "status": PENDING,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(record))
    return record


def decide(request_id: str, decision: str, directory: Optional[Path] = None) -> Dict[str, Any]:
    """Record the owner's decision. Only a pending request can be decided."""
    if decision not in _DECISIONS:
        raise ValueError(f"decision must be one of {sorted(_DECISIONS)}")
    directory = directory or approvals_dir()
    record = read(request_id, directory)
    if record["status"] != PENDING:
        raise ValueError(f"approval request {request_id} is already {record['status']}")
    record["status"] = decision
    record["decided_at"] = datetime.now(timezone.utc).isoformat()
    _path(request_id, directory).write_text(json.dumps(record))
    return record


def read(request_id: str, directory: Optional[Path] = None) -> Dict[str, Any]:
    directory = directory or approvals_dir()
    return json.loads(_path(request_id, directory).read_text())


def is_approved(request_id: str, directory: Optional[Path] = None) -> bool:
    """Fail closed: a missing or unreadable request counts as not approved."""
    try:
        return read(request_id, directory)["status"] == APPROVED
    except (OSError, ValueError, KeyError):
        return False


def list_pending(directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    directory = directory or approvals_dir()
    if not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if record.get("status") == PENDING:
            out.append(record)
    return out
