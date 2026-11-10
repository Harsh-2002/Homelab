# Project instructions for Atlas

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

## Delegation

- Atlas may delegate independent research, verification or isolated implementation.
- Subagents cannot spawn subagents.
- Do not parallelize writes to the same files.
- The final answer belongs to Atlas; subagent output is evidence, not a conclusion.
