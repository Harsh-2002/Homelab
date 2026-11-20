# Checks

Run after `./install.sh` and a reload.

- `./check-models.sh` passes: all 13 approved models are available.
- `opencode models` lists exactly the 13 approved models, no OpenCode free model and no other Go model.
- Each plugin entry's variants and default match `opencode api get /api/model` (compare the `CATALOG` in `plugins/model-allowlist/index.ts` with the server).
- A model reference with an invalid variant is normalized to that model's default; an unapproved model in a `subagent` call becomes `opencode-go/deepseek-v4.1-flash#max`.
- `~/.config/opencode/agents/` holds no custom agents, `default_agent` is not set in `opencode.json`, `model` is `opencode-go/deepseek-v4.1-flash#max`, and a new session starts as OpenCode's stock Build on that model (not Astra).
- Asking a session to "use a subagent with `<model>`" starts a built-in `general` or `explore` subagent on that model, and nothing is delegated unless asked.
- `openai/gpt-6.2-astra`, `openai/gpt-6-astra` and `claude-agent/claude-fable-5-2` are used only when the user asks or a cheaper model already failed, with the reason stated.
