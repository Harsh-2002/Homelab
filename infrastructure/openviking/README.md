# OpenViking shared memory

## Current single-node restoration — 2 November 2026

Current deployment is Portainer stack `memory`174 on Debian `l3b`, with containers
`openviking` and `ollama`, no host1933 publication, and bot mode disabled. The
original memory/index/model/account state was restored unchanged from the backup
before startup. Local embeddings, VLM, queue health and semantic retrieval pass.
Native OpenCode uses the official V2-compatible plugin2026.11.1, one plugin-owned
MCP, and all three bundled skills. The owner chose automatic transcript capture
with tested redaction filters. Codex/Claude clients were not restored.

See [current memory runbook](../l3b/MEMORY.md),
[current Compose](../l3b/memory.compose.yaml), and
[verification](../l3b/MEMORY-VERIFICATION-2026-11-02.json).
Everything below describes the retired deployment unless explicitly confirmed
by that current runbook; do not apply the historical LAN port or agent setup.

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

### SessionCommit read guard and recovery (2026-10-13)

The queue incident and validation boundaries are recorded in [RCA-2026-10-13.md](RCA-2026-10-13.md). Portainer stack 151 now adds one read-only module override to the existing v0.4.22 image. [hotfixes/session_commit_processor.py](hotfixes/session_commit_processor.py) is the installed processor with a narrow change: acquire the existing exact session PathLock around `session.load()`, release it in `finally`, and run Phase 2 after release. This prevents the consumer's early root read from overlapping the producer's locked Phase-1 rewrites. It does not change models, extraction policy, API keys, stored formats, or queue settlement semantics.

The module and its regression test are installed under `/data/apps/openviking/state/hotfixes/`. The compose bind targets the v0.4.22 Python 3.13 package path. Do not carry this full-file override into another release without rebasing and testing against that release; it could otherwise shadow upstream fixes. To reinstall from this repo, copy the two tracked hotfix files to that protected directory, run `docker exec openviking python /app/.openviking/hotfixes/test_session_commit_processor.py`, then redeploy the tracked Compose through Portainer with existing stack environment preserved. Never print stack secrets.

A single protected, consistent pre-cutover state backup is retained at `/data/apps/openviking/recovery-before-queue-read-guard/state` (parent mode 0700). It includes credentials, so do not share or import it into agent memory. It was prepared live and finalized/verified while OpenViking was gracefully stopped. Ollama was not restarted. The API returned healthy 23.39 seconds after the cutover began. OpenViking's native startup recovery reclaimed the four stranded queue deliveries; no direct queue edits or queue clear operation were performed.

For code rollback, remove only the added processor bind from the Portainer Compose and redeploy the same official image with existing environment/volumes. Do not overwrite live state from the backup to undo a code change: that would discard legitimate post-cutover writes. Full state restore requires a separate coordinated recovery plan. Preserve raw archived messages even when a provider call fails. A green queue indicator means no active queue errors under its current rule, not that every historical extraction succeeded or the backlog is empty.

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

## v0.5.3 attempt and rollback, 8 November 2026

v0.5.3 was deployed and rolled back the same night. On it, memory extraction
returned an empty result (7-token model reply, zero memories) even though search,
reads, MCP and the model credential all worked, so v0.4.22 with the
`session_commit_processor.py` hotfix remains the production version. The hotfix
mount must stay while on v0.4.22 and must be dropped, not carried over, on any
v0.5.x. Details, evidence and the pre-retry test are in
[../l3b/UPGRADE-2026-11-07.md](../l3b/UPGRADE-2026-11-07.md). Ollama is now
0.40.15; the `all-minilm` embeddings are unchanged.

Health check for extraction after any change: commit a short note and confirm
`GET /api/v1/sessions/<id>` shows `memories_extracted` with at least one write or
edit and a `completion_tokens` value well above single digits.

## Recall tuning for OpenCode and Hermes, 8 November 2026

Why: agents seemed to ignore memory. Measured on this host, OpenCode injected
recall 377 times since 1 Nov (about 5 entries, 970 tokens each), mostly as
abstracts, and often off-topic. Probing the live search with ten realistic
prompts showed scores of 0.6-0.83 and the correct top hit for 7 of 10, so the
default relevance cutoffs (OpenCode 0.35, Hermes 0.15) filtered nothing.
Retrieval itself is acceptable with `all-minilm`; the cutoffs were the problem.
The server, embedder and extraction model are unchanged (v0.4.22 + hotfix).

Changes (client side only, no server restart):

| Where | Setting | Old | New |
|---|---|---|---|
| `~/.openviking/ovcli.conf` `plugin` (OpenCode) | `scoreThreshold` | 0.35 default | 0.62 |
| | `recallLimit` | 6 | 5 |
| | `recallPreferAbstract` | true default | false (top hits injected as text) |
| | `recallMaxContentChars` | 500 default | 900 |
| | `recallDedupTurns` | 5 default | 8 |
| `~/.hermes/config.yaml` `memory.openviking` | `recall_score_threshold` | 0.15 default | 0.62 |
| | `recall_limit` | 6 default | 5 |
| | `recall_full_read_limit` | 2 default | 3 |
| | `recall_max_injected_chars` | 4000 default | 5000 |

`captureFilters` (secret redaction) are unchanged. Settings load when an agent
starts, so running sessions keep the old values until restarted. To revert,
delete these keys; defaults return.

Findings that are not faults:

- `flushAll` commits are by design: the v2 plugin force-commits every tracked
  session whenever its instance is disposed. Sessions with nothing pending do
  not create server tasks (about 60 real commit tasks in two days).
- Claude Code is connected by MCP only; this is intentional because OpenCode and
  Hermes are the main agents.
- Hermes recall runs before each model call under a 4 s budget; live search
  answers in tens of milliseconds.

Open items:

- The OpenCode session-state file shows 83 ENOENT rename errors (2-7 Nov) even
  though the installed code serializes saves; likely several OpenCode
  processes sharing one state file. Harmless so far (state is rebuilt).
- Weak spot: infrastructure facts that live only in repo runbooks (for example
  the Caddy build) are not in memory, so recall cannot find them. Search the
  repo for those.
- Embedder swap (for example nomic-embed-text or bge-m3) needs an
  `admin_reindex`; only worth trying on an isolated copy if the tightened
  cutoffs do not help.
- Not upgrading to 0.5.x until a release after 0.5.3 contains #6977 and a fix
  for #7099 (extraction deleting root memory files).

## Experience memory, compile and log import, 8 November 2026

Asked to set up three unused features. Outcome on v0.4.22:

| Feature | Result |
|---|---|
| Experience memory | **Enabled.** `server.agent_evolution.enabled = true` in `ov.conf` (top-level `agent_evolution` is ignored; the server reads it from the `server` section). Commit results now report `agent_evolution_enabled: true` and effective types include `cases`, `trajectories` and `experiences`. A deliberately small synthetic session produced no experience (the model extracts a "case" only from substantial tool-using work), but the first real experience, `memories/experiences/shared_skill_installation.md` (Situation/Approach/Reflect, from the add_skill client-timeout session), appeared within minutes of real OpenCode work, confirming it works. |
| Context compile (`ov compile`) | **Enabled.** Stack env `OPENVIKING_WITH_BOT` is now `"1"` (VikingBot runs inside the openviking container and inherits the root `vlm`, including the Codex login). `GET /api/v1/compile/capabilities` reports `configured: true, can_create: true`. Shared skills `llm-wiki`, `knowledge-graph`, `knowledge-distillation`, `daily-report` are installed under `viking://agent/skills` from the OpenViking v0.4.22 tag. A test compile of the Nivra project record finished in 72 s with 2 pages, no warnings; the test output was deleted. |
| Log import (`openviking-server ingest`) | **Not enabled: nothing to import.** Hermes keeps no per-session log files (its `sessions/` directory holds only an index and the importer reads JSONL). OpenCode v2's database has no `session`/`message`/`part` tables, which the importer's adapter expects, and it only goes back to 1 Nov, already captured live. No Claude Code or Codex logs exist on this host. |

Caveats:

- VikingBot runs its agent loop with the sandbox disabled, **inside the
  OpenViking container** (see the bot-mode note above). Compile jobs run only
  when someone submits one with a valid key; the Caddy route stays private.
  Revert with `OPENVIKING_WITH_BOT: "0"` through Portainer if this is unwanted.
- Compile and experience extraction add model calls on the Codex login. The
  test compile used about 83 k input tokens for a 56 KB source.
- During the change memory was unavailable for about a minute while stack 174
  redeployed. Previous compose text is in the Portainer backup made by
  `portainer/stack-update.py`.
- A test commit added one accurate line to `homelab_deployment.md` ("resend the
  existing Env when updating a Portainer stack through the API"); it was kept.
  All other test data was deleted.

## Skills: one source of truth, 8 November 2026

OpenCode and Hermes load skills from `~/.agents/skills`. OpenViking also had
copies of `microsandbox`, `opentunnel`, `rust-best-practices`, `rust-port` and
`rust-review` under `viking://agent/skills` (bodies and reference folders
identical to local). They were redundant: the plugin injected a second skill
catalog at every session start and skill files appeared in recall as noise.

- The five duplicates were removed from OpenViking; the local copies are the
  source of truth. To share one again, `add_skill` it from its local path.
- Kept in OpenViking: `llm-wiki`, `knowledge-graph`, `knowledge-distillation`,
  `daily-report`, because `ov compile` needs a `viking://` skill URI and they
  have no local copy.
- `ovcli.conf` `plugin.opencode.skillCatalog = false` (no duplicate catalog) and
  `plugin.recallExcludeUris` lists `viking://agent/skills` and the user's
  `skills` and `resources` directories (never returned by auto-recall).
