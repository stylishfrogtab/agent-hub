# agent-hub

Fork of [CLI Agent Orchestrator](https://github.com/awslabs/cli-agent-orchestrator) (Apache-2.0; see LICENSE and NOTICE), extended to control Claude Code and Codex from one dashboard.

## Planned features (in priority order)

1. Agent-to-agent delegation with a short brief plus a pointer to shared files or a git worktree (no pasted transcripts). CAO's `assign` and `use_worktree` are the base.
2. "Needs you" flag from Claude Code permission and stop hooks and Codex's notify hook.
3. Approval gate: delegated work that edits files or runs commands waits for owner approval. Not in CAO today.
4. Usage alerts at 80% and 95%: Claude Code status-line file; Codex reader to be verified against `/status`. macOS notifications; optional phone push.

## Status

Initial commit only. No feature code yet. Nothing is installed on the owner's Mac.

## Secrets

None in this repo. Use environment variables or the macOS Keychain.
