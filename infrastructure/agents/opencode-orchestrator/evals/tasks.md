# Evaluation tasks

Run each task twice: once with the single `atlas` and once with Atlas plus the relevant subagents. Record success, tokens, latency, tool errors and whether delegation was appropriate.

| # | Task | Acceptance | Expected delegation |
|---|---|---|---|
| 1 | Fix a one-file Rust bug with a failing unit test | Test passes; no unrelated edits | Atlas does it; verifier optional |
| 2 | Add a Go HTTP endpoint with validation and tests | Endpoint behavior matches the spec; tests pass | Atlas or implementer; verifier |
| 3 | Add a TypeScript/Node feature touching two modules | Types pass; tests pass; no unrelated refactor | Atlas or implementer; verifier |
| 4 | Refactor a JavaScript module without behavior change | Existing tests pass; diff is behavior-preserving | Atlas or implementer; verifier |
| 5 | Write an integration test against a disposable database | Test runs in isolation; cleanup works; deterministic | Implementer writes test; verifier runs it |
| 6 | Add a Playwright E2E test for a login flow | Test passes; no production data; screenshot/evidence | Implementer writes; verifier runs |
| 7 | Review a security-sensitive auth change | Findings ranked; scope respected; no false claims | Security; verifier |
| 8 | Investigate a flaky integration test | Root cause identified with evidence; no guesswork | Explorer + verifier |
| 9 | Update documentation and migration notes | Accurate, concise, links valid | Lead or docs skill; no subagent |
| 10 | Answer a simple one-file question | Correct answer; no unnecessary delegation | Atlas only |

## Metrics

- Acceptance criteria met.
- Tests and QA evidence.
- Routing accuracy: delegated when useful, not delegated when unnecessary.
- Tokens and wall-clock time versus the single-Atlas baseline.
- Handoff loss: missing constraints, wrong files, invented facts.
- Security true positives and false positives.

## Rule

Keep a subagent only if it improves quality, cost, latency or safety on at least one category. Remove agents that do not earn their place.

## Guardrail checks (run before functional eval)

- `opencode models` returns only the approved ten models.
- A subagent call with a non-approved model falls back to DeepSeek V4.1 Flash; a call with no model uses the subagent default.
- `verifier` creates a disposable worktree and leaves the main checkout unchanged.
- A session created before the rename identifies as Atlas through the `build` compatibility profile.
- The model picker shows the ten approved models in a new web/TUI session.
