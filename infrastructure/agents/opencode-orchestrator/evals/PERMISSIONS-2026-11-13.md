# Automatic subagent permissions verification

Owner requested automatic execution without repeated tool approvals across
workspaces. Updated Forge, Scout, Vouch, Shield and Juror; installed copies
match tracked profiles. No server restart, auth change, model change, or global
configuration rewrite was performed.

Independent Vouch verification in a disposable worktree:

- `python3 infrastructure/agents/opencode-orchestrator/evals/permissions.py`:
  three tests passed, including workspace-ask override and retained role denies.
- All five installed profiles matched repository files.
- Harmless shell smoke completed without an approval prompt.
- The worktree was removed.

The tests simulate ordered permission rules; they do not comprehensively test
the OpenCode permission engine or every MCP action. Existing hard policies can
still deny actions. Shell permissions are not an OS sandbox.

Required `python3 infrastructure/agents/check-integrations.py` failed because
the script requires absent `~/.codex/config.toml`. Vouch confirmed Claude,
Hermes and OpenCode configs parsed without exposing their contents. Codex is
retired/outside restore scope; no config was restored to satisfy this check.

The default worker provider rejected the first verification attempt due to its
monthly quota; verification used approved `openai/gpt-6-luna#high` instead.
