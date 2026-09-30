# OpenViking shared memory

OpenViking v0.4.22 runs as Portainer stack `openviking` on `ctr` (10.1.1.4). Caddy serves `https://memory.l3b.cc.cd` privately; its MCP endpoint is `https://memory.l3b.cc.cd/mcp`. Web Studio uses bot mode for Agent chat and is protected by Pocket ID OIDC through Tinyauth on `/studio` and `/studio/*`. Only OpenViking port 1933 is published to the LAN address. The Ollama embedding service is internal to the Compose network. No separate database is deployed.

## Configuration and data

| Item | Location |
| --- | --- |
| Portainer stack | `openviking` (endpoint `ctr`) |
| Compose reference | `infrastructure/openviking/compose.yaml` |
| OpenViking configuration | `/data/apps/openviking/state/ov.conf` |
| Root API key | Portainer stack environment variable (not in Git) |
| Codex OAuth state | `/data/apps/openviking/state/codex_auth.json` (0600; not in Git) |
| Memory/index data | `/data/apps/openviking/state/data` |
| Local embedding model | `/data/apps/openviking/ollama` |
| Proxy | `infrastructure/proxy/Caddyfile`, `memory` snippet |

The official v0.4.22 image does not include the optional `llama-cpp-python` runtime for its `provider: local` GGUF embedding backend. We do not rebuild that image. Instead, the official Ollama container serves the 384-dimensional, CPU-only `all-minilm` embedding model over the internal Docker network. The VLM uses the v0.4.22 `openai-codex` provider with `gpt-6-luna` through the existing Codex account. Groq and Cerebras are not configured in this stack. Codex OAuth is only for the VLM; embeddings remain local.

The Portainer stack has only `OPENVIKING_ROOT_API_KEY`, sourced from the existing `OpenViking` item in the HomeLab 1Password vault. No provider API key is needed for Codex OAuth. The Codex CLI login was imported once using `openviking-server init`; its resulting `codex_auth.json` persists on the state bind mount. It must be protected and renewed if the Codex account session expires. Do not commit or print it. The legacy host-side `secrets.env` file used during staging is removed. Keep the root key for administration only. The same vault item stores the account-scoped user key for agents; all agents must use that *same* user key to access the same memory account.

## Operations

After a new Codex login on `dev`, run `sh scripts/refresh-openviking-codex.sh` from this repository. It streams the existing `/home/dev/.codex/auth.json` over SSH into v0.4.22's native credential writer without staging or displaying tokens. The writer locks and atomically replaces only the protected `codex_auth.json`; model configuration, memories and Ollama are unchanged. An optional first argument selects a different local auth file, and `OPENVIKING_SSH_TARGET` defaults to `ctr`. Then run `ssh ctr 'docker exec openviking openviking-server doctor'` and check VLM and embedding probes. On 2026-09-30, this refreshed login passed both probes with `gpt-6-luna` and `all-minilm`, without a container restart. This is an explicit refresh operation, not automatic synchronization of future dev logins. OpenViking can subsequently refresh its imported credentials when its external source path is absent inside the container; sharing an OAuth refresh chain with other clients can still require reauthentication.

After a fresh deployment, pull the model once with `docker exec openviking-ollama ollama pull all-minilm`. Verify `docker inspect` health for both containers and `GET /health` on port 1933. Authentication is enforced on `/api/v1/*` and `/mcp` with `Authorization: Bearer <user-key>` or `X-API-Key: <user-key>`.

When upgrading, check the tagged release notes, update the pinned image in Compose, retain both bind-mounted data directories, `ov.conf`, and `codex_auth.json`, and redeploy through Portainer. A restart must not require re-pulling the embedding model or regenerating API keys. Back up `/data/apps/openviking/state` and `/data/apps/openviking/ollama` before a version upgrade. Run `docker exec openviking openviking-server doctor` afterward; its VLM probe verifies Codex OAuth and model access.

For Codex and Claude Code, the official OpenViking integrations can automate recall/capture; MCP alone provides manual tools. Hermes has a built-in OpenViking memory provider. Point each at the same HTTPS endpoint and account-scoped user key, never the root key.

On `dev`, Codex has the official `openviking-memory@openviking` plugin (v0.10.2 from the OpenViking v0.4.22 marketplace) and `features.hooks = true` (Codex 0.159 removed the older `plugin_hooks` flag). The plugin supplies its own MCP proxy plus session-start recall, per-prompt recall, turn capture, pre-compaction commit, and session-end commit; the former standalone MCP entry and header helper were removed to prevent duplicate connections. `/home/dev/.openviking/ovcli.conf` is a 0600 local credential file generated from the existing HomeLab `OpenViking` vault item using `scripts/op-sa inject -i infrastructure/openviking/ovcli.conf.template -o /home/dev/.openviking/ovcli.conf --file-mode 0600`. Never commit or print the resolved file. The template is safe to track. After a fresh plugin install or hook change, open a new interactive Codex session and review/trust the plugin's six hooks; without that trust, MCP works but automatic recall/capture does not. Check with `node /home/dev/.codex/plugins/cache/openviking/openviking-memory/0.10.2/scripts/ov-memory-doctor.mjs`. Automatic capture can store conversation and tool output, including accidentally printed secrets; keep secret values out of prompts/tool output.

Bot mode is enabled because Web Studio Agent chat requires it. The v0.4.22 VikingBot gateway warns that its sandbox is disabled and commands run directly **inside the OpenViking container**. Keep the Caddy route private and the account key limited to trusted agents. The bot chat endpoint rejects unauthenticated requests.

OpenViking v0.4.22 has one active server authentication mode. Its Web Studio explicitly does **not** support native `oidc` mode, so the backend remains in `api_key` mode. Caddy applies Tinyauth/Pocket ID only to the Studio path; API, bot API, and MCP paths continue to require OpenViking's account-scoped key. Tinyauth registers the `memory.l3b.cc.cd` app for the existing infrastructure-admins group in `/etc/tinyauth/tinyauth.env` (tracked example in `infrastructure/pocket-id/tinyauth.env.example`). Browser sign-in with Pocket ID grants access to the Studio shell, but Studio may still require the account key once in its Connection settings for data operations. Do not switch `server.auth_mode` to `oidc` without a separate client migration plan.

## Shared knowledge snapshot

On 2026-09-28, the shared `agents` account was seeded **through the OpenViking MCP tools** with 42 tracked repository Markdown runbooks, 87 sanitized active configuration files, and the full content of the four relevant Notion pages. The large main runbook is split into 20 numbered resources, the BIOS page into two, and the NIC and shareable DNS pages into one each. `viking://resources/homelab/START-HERE.md` is the current-state navigation index; `viking://resources/homelab/OPERATING-STANDARDS.md` records the owner's working conventions and points to the complete Notion snapshots. Repository resources live under `viking://resources/homelab/repo/`; config snapshots live under `viking://resources/homelab/config/`; Notion snapshots live under `viking://resources/homelab/notion/`.

The imported Notion pages are dated history, not a claim that every old instruction remains current. For example, the BIOS page records both the failed old update and the later successful Dell F12 updates, and the DNS page records the later correction to persistent Unbound configuration. Prefer the latest relevant runbook entry and verify live state before any mutation. Secrets, generated Talos machine configurations, environment files, and private keys were not imported. The snapshot is **not automatically synchronized** with Git or Notion; after material changes, update the source runbooks and then refresh affected OpenViking resources with MCP `write`/`edit`. Do not treat search results alone as proof of current deployment state.

The [official Codex integration guide](https://docs.openviking.ai/en/agent-integrations/04-codex) describes the installed plugin's session/prompt/stop hooks. All six hooks were reviewed and trusted in Codex on 2026-09-29. A fresh `codex exec` visibly ran SessionStart, UserPromptSubmit, and Stop hooks; `ov-memory-doctor.mjs` then reported committed captured turns, valid trust records, endpoint authentication, MCP tools, and server readiness. Their automatic transcript capture is privacy-sensitive. Do not trust a changed hook definition without reviewing it.

The dated [current-state and open-issues note](CURRENT-STATE.md) records live verification separately from the historical import. Read it after `START-HERE.md`, then recheck the relevant hosts before acting. Its 2026-09-28 ISO/backup findings are historical; see its 2026-09-29 follow-up for the verified recovery and remaining backup limitations.
