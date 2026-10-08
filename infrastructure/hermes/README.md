# Hermes Agent on dev

Home Assistant integration is active through `HASS_URL=http://10.1.1.13` and `HASS_TOKEN` in the mode-0600 live `.env`. The owner-provided long-lived token is also stored as a concealed field in the existing `Home Assistant` HomeLab 1Password item. The same token powers Homepage's native Home Assistant widget through a separate Kubernetes Secret. The gateway was restarted and a token-authenticated Home Assistant API state read succeeded. The `homeassistant` toolset is enabled in Hermes; an agent session may need `/reload-mcp` or a new session to see newly available tools. No token is kept in Git.

Hermes Agent runs under the existing `dev` Linux account on `dev`, not a separate OS user. This deliberately reuses that account's Git, SSH, `gh`, and Codex CLI authentication. It also means Hermes has the same filesystem and command privileges as `dev`; do not grant Telegram access to anyone other than the owner's numeric Telegram user ID. The official installer creates the isolated Python/runtime tree under `/home/dev/.hermes/hermes-agent` and keeps Hermes configuration and sessions under `/home/dev/.hermes`. No browser/computer-use extras are installed. The working installation is v0.21.5 plus upstream main commit `09581caca` (2026-09-29); pinning the v0.21.5 tag failed because that tag lacks `pm/lock.json` and `pm.cli` required by the current installer, so the installer was rerun on main and validated.

Cloudflare CLI access was verified on 2026-10-08: the owner's separately installed `cf` (`1.0.0-beta.13`) is OAuth-authenticated under `dev`. The active Hermes gateway has `HOME=/home/dev` and `/usr/local/bin` on PATH, so it can reuse `cf` and its mode-0600 `/home/dev/.config/cloudflare/config/default.json` without another secret in `.hermes/.env`. Never display or copy that credential file into memory, prompts, or Git. Check `cf auth whoami` before operations, since authentication can expire. `cfdns` remains the independent minimal DNS helper; do not confuse the two. Other hosts/users need their own authentication. See [Cloudflare CLI access for agents](../proxy/README.md#cloudflare-cli-access-for-agents).

The model provider is `openai-codex` with `gpt-6-luna` and `agent.reasoning_effort: medium`. The existing Codex CLI login was imported into Hermes' own protected auth store via `hermes model`; a one-shot CLI model call succeeded. Groq is used **only** for incoming Telegram voice transcription (`stt.provider: groq`, `whisper-large-v3-turbo`, language auto-detect), not for chat inference. A real audio-file call to Groq's transcription API succeeded. The live `/home/dev/.hermes/.env` is mode 0600 and contains additional Photon and Home Assistant settings beyond this directory's bootstrap `.env.template`; never re-inject the template over the live file or those settings and `GITHUB_TOKEN` will be lost. Never put resolved keys in Git, chat, or command output. The `Groq API Key` vault item remains the source of truth. Hermes reads `stt.provider` and `agent.reasoning_effort` despite its `config set/get` schema warning for those keys; verify runtime behavior on upgrade.

Hermes' built-in OpenViking memory provider connects to `https://memory.l3b.cc.cd` with the same account-scoped agent key as Codex, injected from the `OpenViking` HomeLab vault item. The root API key is not used by Hermes. `hermes memory status` reports the plugin installed, active, and available. The provider's OpenViking search/read/remember tools are available to Hermes; ordinary built-in memory additions are mirrored by the provider, while replace/remove are not automatically mirrored.

The existing Telegram bot is `@heyhermesai_bot`. Its token is stored in the single HomeLab vault item `Hermes Telegram Bot` field `credential`; the owner's **numeric** ID is in `allowed-user-id`. The gateway environment sets `TELEGRAM_ALLOWED_USERS` to that ID, never a username or `*`. The bot token was verified with Telegram `getMe`, and the gateway connected in polling mode. Because the original token was pasted into chat, rotate it with BotFather, update the vault item, re-inject `.env`, and restart the gateway. Do not confuse the existing `Hermes Agent` vault item (mobile app login) with the Telegram bot token.

The only gateway is the `dev` user service `hermes-gateway.service`; `loginctl` linger is enabled so it starts after host reboot and survives logout. No public inbound port or Caddy route is needed. Check `hermes gateway status` and `journalctl --user -u hermes-gateway --no-pager -n 80`. At the owner's request, `GITHUB_TOKEN` in the protected live `.env` is a copy of the current `gh auth token` for the `Harsh-2002` login. It was compared byte-for-byte without printing either value; `hermes doctor` confirmed the env token was accepted by `api.github.com`. Refresh this copy if the `gh` login token rotates. Web search uses `web.search_backend: openai-native` through Codex OAuth; URL extraction retains the default keyless Firecrawl backend.

Photon/iMessage is also configured in the same live `.env`; `hermes photon status` reports stored device/project credentials and installed sidecar dependencies, and the Node sidecar listens on loopback port 8789. The gateway currently logs `target_not_allowed` for its startup notification to the owner's number: Photon's shared/free line cannot initiate a conversation with a new target. Text the assigned Photon iMessage line once from the allowed phone number before expecting outbound notices or replies. Do not remove the `PHOTON_*` keys while changing Telegram or GitHub settings.

`TELEGRAM_HOME_CHANNEL` is set to the owner's numeric Telegram ID and `TELEGRAM_HOME_CHANNEL_NAME` to `Hermes` in the protected `.env`. This is the proactive/cron delivery destination, not the only conversational channel. Photon is connected, but its shared line needs the owner to send the first iMessage before proactive replies can work. Restart `hermes-gateway.service` after editing either home-channel setting.

The private dashboard runs as `hermes-dashboard.service` under the same `dev` user at `10.1.1.5:9119`, behind the existing Caddy route `https://hermes.l3b.cc.cd`. Pocket ID OIDC uses the public PKCE client `hermes-dashboard` restricted to the `infrastructure-admins` group, with callback `https://hermes.l3b.cc.cd/auth/callback`. The live clean YAML is `/home/dev/.hermes/config.yaml`; its pre-cleanup reference is `/home/dev/.hermes/config.yaml.before-cleanup-2026-09-29`. The cleanup removed only comments and blank lines and preserved the parsed active configuration byte-for-byte. No client secret is used. Caddy keeps this route private; do not publish it casually because the dashboard can operate Hermes. Verify with `systemctl --user status hermes-dashboard` and `curl https://hermes.l3b.cc.cd/api/status`: `auth_required` must be true and `auth_providers` must contain `self-hosted`. Browser sign-in still requires a human test.

The active YAML now has no comments, including inline comments. `agent.disabled_toolsets` explicitly excludes `x_search`, `video_gen`, `spotify`, `video`, `discord`, `discord_admin`, and `yuanbao`; their stale entries and unused Discord/Yuanbao platform mappings were removed. These names remain in the denylist so an installed plugin or composite toolset cannot silently re-enable them. `updates.check: true` shows passive update notices; it does not install updates automatically. Do not add an unattended `hermes update` timer without testing the upgrade and plugin restart path; the gateway and dashboard are separately managed user services.

Search stays `web.search_backend: openai-native` via Codex OAuth and extraction is pinned to `web.extract_backend: firecrawl`. `TAVILY_API_KEY` is a protected copy of the single `Tavily API Key` HomeLab vault item, tested with a real one-result Tavily search. It is standby, not an automatic secondary search: Hermes does not support a keyed Tavily failover behind OpenAI Native, whose search runs on the Codex server. If OpenAI Native must be replaced, set `web.search_backend: tavily` and restart the gateway and dashboard; restore `openai-native` afterward. Do not claim that merely storing the Tavily key activates failover. The key was pasted into chat, so rotate it in Tavily and update the same vault item and protected `.env` later.

Hermes personal context is split deliberately: `/home/dev/.hermes/SOUL.md` holds behavior, `memories/USER.md` holds compact durable user context, and `memories/MEMORY.md` holds memory hygiene. The richer shared profile and career/project context are `viking://user/iam-anuragvishwakarma/memories/anurag-profile.md` and `viking://user/iam-anuragvishwakarma/memories/anurag-context.md` in OpenViking; search and read were verified after the 2026-09-29 update. They contain no keys, exact home address, salary or transient infrastructure state. Latest user instructions and current project runbooks override profile memory. Do not overwrite these files with an old template during a Hermes upgrade.

At the owner's explicit request, `approvals.mode: off` is set persistently in `/home/dev/.hermes/config.yaml` for full command-approval bypass in CLI and Telegram sessions. Hermes' non-bypassable hardline blocklist still applies. This is high-trust access to the entire `dev` account, including SSH, GitHub, and the service-account vault helper; keep the Telegram allowlist to the single numeric owner ID, rotate the exposed bot token, and do not add other bot users casually. Check with `hermes config get approvals.mode`; to restore guarded behavior, set `smart` and restart `hermes-gateway.service`.

After rotating the bot token, update only the `credential` field of the existing `Hermes Telegram Bot` item and the `TELEGRAM_BOT_TOKEN` line in the protected live `.env`, preserving all other lines. Then run:

```sh
systemctl --user restart hermes-gateway
hermes gateway status
```

Update the pinned Hermes release deliberately after reviewing its release notes, then recheck Codex auth, OpenViking memory, Groq STT, and Telegram access. Never place secrets in tracked configuration or automatic memory transcripts.

## shadcn MCP integration (2026-10-04)

Codex and Hermes on dev both have an MCP server named `shadcn`, using the official stdio command `npx -y shadcn@latest mcp`. Codex stores it in `~/.codex/config.toml`; Hermes stores it in `~/.hermes/config.yaml` under `mcp_servers`. Existing servers and credentials are preserved. No API key, public port, Docker service or reverse proxy is required for the public registry.

Restart Codex to load the new server. Hermes can reload MCP connections or restart its user gateway/dashboard services. Registries are selected from the active project's `components.json`; do not pin the server working directory to the homelab repository or initialize UI components here. The public `@shadcn` registry works without custom credentials. Private registries need their own project-specific authentication.

The upstream-recommended `@latest` is intentional and may resolve newer CLI releases later. On setup, npm resolved shadcn 4.21.1. Check registry search and tool discovery after future changes. Source: [official shadcn MCP documentation](https://ui.shadcn.com/docs/mcp).

Validated stdio initialization, seven tools, and a real public-registry `button` search returning results. The 4.21.1 search result has an upstream formatting defect (`[object Promise]` in inline add-command hints); component search itself succeeds. Do not copy those hints as shell commands. No project components were installed during verification.

## Karakeep CLI integration (2026-10-03)

Hermes uses the official `@karakeep/cli@0.33.2`, not an additional MCP server, to manage the owner's bookmarks at https://pin.l3b.cc.cd. The package lives in `/home/dev/.local/share/karakeep-cli`; `/home/dev/.local/bin/karakeep` is on the gateway's existing PATH.

The dedicated key is saved in HomeLab → Karakeep → `Hermes API Key`, with its ID and scopes in adjacent fields. It was created through native Karakeep authentication using the existing vault login. Its scopes are `users:read`, `bookmarks:readwrite`, `lists:readwrite`, `tags:readwrite`, `highlights:readwrite`, and `assets:readwrite`, without administrative access. Do not generate another key during routine setup or put it in Git, prompts, or memory.

The CLI reads `/home/dev/.config/karakeep/config.json` (0600, parent directory 0700). No additional `.hermes/.env` secret or shell export is necessary. Preserve this file across upgrades; restore its secret from the same vault field if needed.

The official skill from `karakeep-app/karakeep`, tag `v0.33.2`, is installed at `/home/dev/.hermes/skills/productivity/karakeep/SKILL.md`. A small local section tells Hermes to reuse the protected CLI configuration, avoid printing credentials, resolve IDs before modifications, and use positional `lists get <id>` syntax. Preserve that section when updating the upstream skill.

Validation passed: native account authentication, temporary text bookmark creation/update/read, tagging, private list creation/membership, full-text search and tag-filtered search. Only the temporary test bookmark, tag and list were deleted afterward. These tests validate the CLI integration, not a live Telegram/iMessage conversation.

Search initially failed because the Karakeep app service did not receive `MEILI_MASTER_KEY`, although Portainer already supplied the secret to Meilisearch. Added the missing environment mapping in the tracked Compose and updated stack 80 through the Portainer API, preserving existing environment values without an image pull. Retesting confirmed actual indexing and retrieval. Keep this mapping on future redeployments; no database/index reset was needed.

Useful checks, without exposing credentials:

```sh
karakeep --version
karakeep --json whoami
karakeep --json bookmarks search 'your search terms' --limit 5
stat -c '%a %n' /home/dev/.config/karakeep /home/dev/.config/karakeep/config.json
```

Sources: [official CLI](https://docs.karakeep.app/integrations/command-line/), [official agent skill](https://github.com/karakeep-app/karakeep/tree/v0.33.2/skills).
