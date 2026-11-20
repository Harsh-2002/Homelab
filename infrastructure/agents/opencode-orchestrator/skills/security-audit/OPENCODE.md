# OpenCode adapter

This is the Cloudflare `security-audit` skill, vendored for OpenCode V2. The upstream workflow is platform-neutral; this file maps its terms to this installation. No custom agents are installed, so the built-in ones are used.

| Upstream term | OpenCode mapping |
|---|---|
| Parent | The current session (the agent the user is talking to) |
| Task tool | `subagent` tool |
| `research` agent | built-in `explore` subagent, read-only source exploration and critics |
| `general` hunter | built-in `general` subagent, instructed to stay read-only against the target |
| `general` verifier | built-in `general` subagent, a separate one from the hunter, instructed to re-read the source independently |
| `subagent_type:` | the `agent` argument of a `subagent` call |

## Full audit mode

- Full audit mode needs subagents, so **run it only when the user explicitly asks for a full audit** and authorizes the scope. Otherwise use guidance mode for a focused review.
- The parent session is the only parent. It must follow the upstream write-isolation, coverage-ledger, candidate-validation and reporting rules.
- Subagents cannot spawn subagents. A hunter or verifier may load this skill in guidance mode only.
- Built-in subagents have normal tool permissions, so the read-only and no-production rules are **instructions in the brief, not enforced limits**. State them explicitly in every brief: stay read-only against the target, use a disposable microsandbox for any bounded local check, never read credentials, `.env` files or auth stores.
- Do not probe production, deployed endpoints, shared infrastructure or credentials. Use a disposable worktree or microsandbox; if the required isolation is unavailable, keep the lead as `needs_validation`.

## Output

Use an output directory outside the target, defaulting to `~/security-audit-skill/<repo-name>/run-<N>`, unless the user explicitly chooses a version-control-ignored directory. The parent owns all shared files and retained artifacts.
