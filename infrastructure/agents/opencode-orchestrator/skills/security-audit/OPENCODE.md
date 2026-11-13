# OpenCode adapter

This is the Cloudflare `security-audit` skill, vendored for the Atlas OpenCode V2 team. The upstream workflow is platform-neutral; this file maps its terms to this installation.

| Upstream term | OpenCode mapping |
|---|---|
| Parent | **Atlas** (primary agent) |
| Task tool | `subagent` tool |
| `research` agent | **Scout** (`scout`) — read-only source exploration and critics |
| `general` hunter | **Shield** (`shield`) — authorized security review, read-only with sandboxed shell |
| `general` verifier | **Vouch** (`vouch`) — independent verification, read-only with sandboxed shell |
| `subagent_type:` | the `agent` argument of a `subagent` call |

## Full audit mode

- **Atlas is the only parent.** It is the primary agent with the required subagent permissions. It must follow the upstream write-isolation, coverage-ledger, candidate-validation and reporting rules.
- **Shield cannot run full audit mode itself.** It is a subagent and cannot spawn hunters or verifiers. It may load this skill in guidance mode for focused reviews; hand a full codebase audit to Atlas.
- **Scout** is the `research` role: source-only reconnaissance and coverage critics. It does not run target code.
- **Shield** is the `general` hunter role. It stays read-only against the target and uses a disposable microsandbox for any bounded local check.
- **Vouch** is the `general` verifier role. It independently re-reads source and reproduces decisive checks where safe.
- Full audit mode requires explicit user authorization. Do not probe production, deployed endpoints, shared infrastructure or credentials. Use a disposable worktree or microsandbox; if the required isolation is unavailable, keep the lead as `needs_validation`.

## Output

Use an output directory outside the target, defaulting to `~/security-audit-skill/<repo-name>/run-<N>`, unless the user explicitly chooses a version-control-ignored directory. The parent owns all shared files and retained artifacts.
