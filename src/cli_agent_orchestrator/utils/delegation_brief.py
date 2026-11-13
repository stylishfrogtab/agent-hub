"""Reject delegation messages that are transcripts instead of briefs.

A brief is a short task plus a pointer to where the work lives (a file path or
a worktree). A pasted chat transcript is neither. This check runs before a
worker is created, so the supervisor gets the error instead of a worker that
starts with a wall of someone else's conversation.

shortcut: fixed size cap and speaker-label heuristic, tune after real use.
"""

import re
from typing import Optional

#: Longer than this and the message is treated as pasted material, not a brief.
MAX_BRIEF_CHARS = 4000

#: Lines that start like a chat log ("User: ...", "Assistant: ...").
_SPEAKER_LINE = re.compile(r"^\s*(user|assistant|human|ai|claude|you)\s*:", re.IGNORECASE)
_SPEAKER_LINE_LIMIT = 3


def check_delegation_brief(message: str) -> Optional[str]:
    """Return a refusal reason for a non-brief message, or None when it is fine."""
    if len(message) > MAX_BRIEF_CHARS:
        return (
            f"Delegation message is {len(message)} characters (limit {MAX_BRIEF_CHARS}). "
            "Write the details to a file or worktree and send a short brief that points to it."
        )
    speaker_lines = sum(1 for line in message.splitlines() if _SPEAKER_LINE.match(line))
    if speaker_lines >= _SPEAKER_LINE_LIMIT:
        return (
            "Delegation message looks like a pasted chat transcript. "
            "Send a short brief with a pointer to the shared file or worktree instead."
        )
    return None
