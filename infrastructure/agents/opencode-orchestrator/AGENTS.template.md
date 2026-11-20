# Project instructions

Copy this file to the project root as `AGENTS.md` and add repository-specific rules. Keep it short; language and framework procedures belong in skills.

## Work

- Read the nearest project instructions, README and build/test commands before editing.
- Load the relevant skill before using a language, framework, test harness or domain procedure.
- Make the smallest useful change. Do not refactor unrelated code.
- Add or update tests when behavior changes.
- Do not weaken tests to make them pass.

## Verification

- Run focused tests first, then the broader suite when practical.
- Use a disposable worktree or microsandbox for independent verification.
- Report exact commands and results. Do not claim a check passed without evidence.

## Subagents

- Do not delegate on your own initiative. Start a subagent only when the user asks for one.
- When asked, use OpenCode's built-in subagents (`general`, `explore`) and the model the user names, as `provider/model#variant`. If no model is named, leave it unset so the subagent uses the session's model.
- Approved models are listed in the `model-catalog` skill; load it when choosing one.
- Subagents cannot spawn subagents. Do not parallelize writes to the same files.
- The parent session owns the final answer; subagent output is evidence to check, not a conclusion.

## Development URLs

Private HTTPS dev URLs map to fixed host ports; use any free one (check with
`devurl`): `https://dev.l3b.cc.cd` -> 4100 (primary), `https://preview.l3b.cc.cd`
-> 4200, `https://sandbox.l3b.cc.cd` -> 4300 (microsandbox/experiments). Bind the
server to `0.0.0.0` or `10.1.3.1`, never loopback; microsandbox publishes with
`-p 10.1.3.1:4300:<guest-port>`. LAN/WireGuard only, no login. Do not add other
hostnames/ports or kill a process you did not start. Load the `dev-urls` skill.
