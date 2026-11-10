# Evaluation tasks

Run each task twice: once with the single `atlas` and once with Atlas plus the relevant subagents. Record success, tokens, latency, tool errors and whether delegation was appropriate.

| # | Task | Acceptance | Expected delegation |
|---|---|---|---|
| 1 | Fix a one-file Rust bug with a failing unit test | Test passes; no unrelated edits | Atlas does it; Vouch optional |
| 2 | Add a Go HTTP endpoint with validation and tests | Endpoint behavior matches the spec; tests pass | Atlas or Forge; Vouch |
| 3 | Add a TypeScript/Node feature touching two modules | Types pass; tests pass; no unrelated refactor | Atlas or Forge; Vouch |
| 4 | Refactor a JavaScript module without behavior change | Existing tests pass; diff is behavior-preserving | Atlas or Forge; Vouch |
| 5 | Write an integration test against a disposable database | Test runs in isolation; cleanup works; deterministic | Forge writes test; Vouch runs it |
| 6 | Add a Playwright E2E test for a login flow | Test passes; no production data; screenshot/evidence | Forge writes; Vouch runs |
| 7 | Review a security-sensitive auth change | Findings ranked; scope respected; no false claims | Shield; Vouch |
| 8 | Investigate a flaky integration test | Root cause identified with evidence; no guesswork | Scout + Vouch |
| 9 | Update documentation and migration notes | Accurate, concise, links valid | Atlas or docs skill; no subagent |
| 10 | Answer a simple one-file question | Correct answer; no unnecessary delegation | Atlas only |
| 11 | Decide between two architecture options with `oracle` | 3 independent votes, tally shown, majority reported | Oracle + 3 jurors |
| 12 | Decide a high-stakes irreversible choice with `oracle` | 5 independent votes, dissent and runoff rules respected | Oracle + 5 jurors |
| 13 | Give `oracle` a deliberately split question | Runoff runs; tie-break is stated if it persists | Oracle + fresh jurors |

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

- `opencode models` returns only the approved eleven models.
- A subagent call with a non-approved model falls back to `opencode-go/deepseek-v4.1-flash#max`; a call with no model uses the subagent default.
- `vouch` creates a disposable worktree and leaves the main checkout unchanged.
- A session created before the rename identifies as Atlas through the `build` compatibility profile.
- The model picker shows the eleven approved models in a new web/TUI session.
- Claude Agent aliases resolve to Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.2 on the installed Claude Code CLI.
- `oracle` is selectable as a primary agent but is not the default; new sessions still start with Atlas.
- `juror` cannot spawn subagents, edit files or run shell commands.
- Every agent default carries a valid `#variant`; no agent default is a bare model.
- A subagent call with a bare allowed model is normalized to that model's default variant, not to DeepSeek.
- A subagent call with an invalid variant is normalized to the same model's default variant.
- Chinese agent defaults use `#max`; OpenAI/Claude defaults use `#medium`.
- `openai/gpt-6-astra` and `claude-agent/fable` are not used for routine work, default workers or whole juries; any use carries a stated justification.
- A default 3/5/7 decision jury excludes Astra and Fable unless the user explicitly requests an exceptional premium seat.
- A bare approved model selected directly in the session picker is normalized to its default variant (e.g. OpenAI Sol → `medium`), not left bare.
- `opencode run --model anthropic/claude-sonnet-5-5` is denied; the `anthropic/*` provider is not usable.
