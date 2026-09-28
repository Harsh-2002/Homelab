# OpenViking shared memory

OpenViking v0.4.22 runs as Portainer stack `openviking` on `ctr` (10.1.1.4). Caddy serves `https://memory.l3b.cc.cd` privately; its MCP endpoint is `https://memory.l3b.cc.cd/mcp`. Web Studio uses bot mode for Agent chat and is protected by Pocket ID OIDC through Tinyauth on `/studio` and `/studio/*`. Only OpenViking port 1933 is published to the LAN address. The Ollama embedding service is internal to the Compose network. No separate database is deployed.

## Configuration and data

| Item | Location |
| --- | --- |
| Portainer stack | `openviking` (endpoint `ctr`) |
| Compose reference | `infrastructure/openviking/compose.yaml` |
| OpenViking configuration | `/data/apps/openviking/state/ov.conf` |
| API keys | Portainer stack environment variables (not in Git) |
| Memory/index data | `/data/apps/openviking/state/data` |
| Local embedding model | `/data/apps/openviking/ollama` |
| Proxy | `infrastructure/proxy/Caddyfile`, `memory` snippet |

The official v0.4.22 image does not include the optional `llama-cpp-python` runtime for its `provider: local` GGUF embedding backend. We do not rebuild that image. Instead, the official Ollama container serves the 384-dimensional, CPU-only `all-minilm` embedding model over the internal Docker network. Groq `openai/gpt-oss-120b` is VLM priority 1; Cerebras `gpt-oss-120b` is priority 2. OpenViking's ordered `vlm.credentials` provides fallback. Neither provider handles embeddings.

The Portainer environment fields are populated from the HomeLab 1Password vault items `Groq API Key`, `Cerebras API Key`, and `OpenViking`. Portainer resolves Compose variables from these fields; the values are not in Git. The legacy host-side `secrets.env` file used during staging is removed once deployment succeeds. Keep the root key for administration only. Create an account-scoped user key for agents and store it in the same vault item. All agents must use that *same* user key to access the same memory account.

## Operations

After a fresh deployment, pull the model once with `docker exec openviking-ollama ollama pull all-minilm`. Verify `docker inspect` health for both containers and `GET /health` on port 1933. Authentication is enforced on `/api/v1/*` and `/mcp` with `Authorization: Bearer <user-key>` or `X-API-Key: <user-key>`.

When upgrading, check the tagged release notes, update the pinned image in Compose, retain both bind-mounted data directories and `ov.conf`, and redeploy through Portainer. A restart must not require re-pulling the embedding model or regenerating API keys. Back up `/data/apps/openviking/state` and `/data/apps/openviking/ollama` before a version upgrade.

For Codex and Claude Code, the official OpenViking integrations can automate recall/capture; MCP alone provides manual tools. Hermes has a built-in OpenViking memory provider. Point each at the same HTTPS endpoint and account-scoped user key, never the root key.

On `dev`, Codex has `[mcp_servers.openviking]` in `/home/dev/.codex/config.toml`, pointing at the HTTPS `/mcp` endpoint. `scripts/openviking-mcp-headers` retrieves the shared user key from 1Password when Codex connects; it does not keep a second plaintext copy. Restart Codex to load the new MCP server. Automatic session recall/capture hooks are **not** installed; that is a separate, broader privacy/behavior choice.

Bot mode is enabled because Web Studio Agent chat requires it. The v0.4.22 VikingBot gateway warns that its sandbox is disabled and commands run directly **inside the OpenViking container**. Keep the Caddy route private and the account key limited to trusted agents. The bot chat endpoint rejects unauthenticated requests.

OpenViking v0.4.22 has one active server authentication mode. Its Web Studio explicitly does **not** support native `oidc` mode, so the backend remains in `api_key` mode. Caddy applies Tinyauth/Pocket ID only to the Studio path; API, bot API, and MCP paths continue to require OpenViking's account-scoped key. Tinyauth registers the `memory.l3b.cc.cd` app for the existing infrastructure-admins group in `/etc/tinyauth/tinyauth.env` (tracked example in `infrastructure/pocket-id/tinyauth.env.example`). Browser sign-in with Pocket ID grants access to the Studio shell, but Studio may still require the account key once in its Connection settings for data operations. Do not switch `server.auth_mode` to `oidc` without a separate client migration plan.

## Shared knowledge snapshot

On 2026-09-28, the shared `agents` account was seeded **through the OpenViking MCP tools** with 42 tracked repository Markdown runbooks, 87 sanitized active configuration files, and the full content of the four relevant Notion pages. The large main runbook is split into 20 numbered resources, the BIOS page into two, and the NIC and shareable DNS pages into one each. `viking://resources/homelab/START-HERE.md` is the current-state navigation index; `viking://resources/homelab/OPERATING-STANDARDS.md` records the owner's working conventions and points to the complete Notion snapshots. Repository resources live under `viking://resources/homelab/repo/`; config snapshots live under `viking://resources/homelab/config/`; Notion snapshots live under `viking://resources/homelab/notion/`.

The imported Notion pages are dated history, not a claim that every old instruction remains current. For example, the BIOS page records both the failed old update and the later successful Dell F12 updates, and the DNS page records the later correction to persistent Unbound configuration. Prefer the latest relevant runbook entry and verify live state before any mutation. Secrets, generated Talos machine configurations, environment files, and private keys were not imported. The snapshot is **not automatically synchronized** with Git or Notion; after material changes, update the source runbooks and then refresh affected OpenViking resources with MCP `write`/`edit`. Do not treat search results alone as proof of current deployment state.

The [official Codex integration guide](https://docs.openviking.ai/en/agent-integrations/04-codex) describes an optional memory plugin with session/prompt/stop hooks for automatic recall and capture. This deployment currently uses the existing authenticated MCP connection only; no transcript-capturing hooks were installed. Installing those hooks is a separate privacy decision, because they can capture conversation and tool output automatically.
