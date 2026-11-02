# Playwright CLI — the only agent browser interface

Updated 2 November 2026.

## Installed

- Global package: `@playwright/cli@0.1.23` in the user npm prefix
  (`/home/dev/.local`), command `playwright-cli`.
- Official skill: `~/.agents/skills/playwright-cli/SKILL.md` (also installed
  through `playwright-cli install --skills agents --global`). The skill includes
  references for tests, tracing, video, storage state, request mocking and
  session management.
- Host Playwright Chromium `157.0.8103.15` at
  `~/.cache/ms-playwright/chromium-1252`.
- Required Debian runtime libraries for Chromium were installed; the browser
  launch was verified, not assumed.

## Use

```bash
playwright-cli -s=ui open https://example.com
playwright-cli -s=ui snapshot
playwright-cli -s=ui find "Sign in"
playwright-cli -s=ui screenshot --filename=/path.png
playwright-cli -s=ui console
playwright-cli -s=ui requests
playwright-cli -s=ui close
```

Reuse the named session for related work; do not launch a second browser for
each step. `playwright-cli list` shows sessions; `close-all` shuts them down.
`open --persistent` stores a profile only when persistence is required. The
CLI is headless by default; use `--headed` only when a visual check needs it.

Official skill: `playwright-cli` (`SKILL.md` plus `references/`). No other
browser MCP or agent-browser framework is permitted.

## Removed or disabled

- OpenCode MCP entries `playwright` and `chrome-devtools`: removed.
- Hermes `playwright` and `chrome-devtools` MCPs: disabled.
- Portainer `tools` stack (ID173) and its `playwright`/MCP container: removed.
- `mcr.microsoft.com/playwright/mcp` image: removed.
- `chrome-devtools-mcp`, `playwright-mcp`, `agent-browser` and Puppeteer-based
  agent tools: not installed/configured.
- Historical browser-MCP scripts and evidence are not current interfaces.

`karakeep-chrome` remains because it is an application dependency of Karakeep,
not an agent-facing browser tool. Project Playwright tests/dependencies remain.

## Validation

See [browser CLI verification](BROWSER-CLI-VERIFICATION-2026-11-02.json).
Actual checks: launch, navigate `https://example.com`, snapshot/element query,
screenshot, console, network (`requests --static`), close; internal
`https://l3b.cc.cd` navigation reached the Tinyauth/Pocket ID login flow with
network and console inspection; no unexpected browser MCPs remain.

The old `verify-*-browser` scripts that used `docker exec playwright` are
MCP-era artifacts. Use Playwright CLI directly for current browser checks; do
not restart the retired tools stack to make them pass.
