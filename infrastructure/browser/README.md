# Browser Use — OpenCode and Hermes

Owner-approved production integration, 10 November 2026. One Portainer stack
**browser**, one service/container **browser**, on the existing `l3b` network.
Native OpenCode/Hermes identities, sessions, memory and other integrations remain
unchanged. No new MCP, cloud-browser account, public endpoint, VM or schedule.

## Components and operation

Routing is agent guidance, not a dispatcher: explicit choice wins; APIs/fetch
for plain reads, Playwright CLI for deterministic tests/debugging, Browser Use
for interactive browsing/forms, and `task` for autonomous whole-task delegation.
Both agents' Browser Use skills carry this rule.

Cleanup audited after deployment: removed the exact three acceptance task
workspaces, local verification uploads/downloads/screenshots and temporary
upstream checkout. Kept the tracked verification record, reproducible source,
runtime profiles/private credentials, and shared Docker caches/unrelated images.
Those are intentional state, not abandoned test artifacts. Future task outputs
are retained for delivery and require scoped cleanup after use.

- Browser Use **1.0.0**, Browser Harness **0.1.13**, Chromium and Python live in
  the image, not in host Python. `requirements.lock` pins installed Python versions;
  `upstream.json` records the official skills repository revision.
- `/data/apps/browser` is the persistent bind on the existing `/data` UUID
  `f3c5b7ac-b0c8-463f-a91a-45e880ebae21`. Profiles, private config and task outputs
  are application data; Docker images/runtime remain on NVMe.
- OpenCode's persistent direct browser uses internal loopback CDP 9222 and
  profile `profiles/opencode`; Hermes uses 9223 and `profiles/hermes`.
- Browser ports are **not published**. No Docker socket or agent auth directory
  is mounted in the container. Host launchers use `docker exec` as the owner.
- The container runs UID/GID1000, drops capabilities, no-new-privileges,
  3 GiB memory / 2 CPU / 768 PID limit, health checks on both browsers and restart
  unless stopped. Tini reaps children. Stale singleton links from the retired
  container are removed only from the two owned profiles during startup.
- Chromium uses `--no-sandbox` in this container. The container boundary is not
  equivalent to a hostile-code microVM. Both agents are trusted same-owner
  processes: profiles are separated for workflow correctness, not separate
  security tenants. The runtime can reach LAN services; do not expose it to
  unrelated users or follow instructions embedded in pages.

### Direct browser tools

OpenCode uses `browser-use`; Hermes uses `browser-use-hermes`. Explicit routing
also works with `browser-use --agent hermes`. Each command obtains a non-blocking
agent-specific file lock, so concurrent commands cannot race in one session.

```bash
browser-use <<'PY'
new_tab('https://example.com')
print(page_info())
PY

browser-use-hermes <<'PY'
new_tab('https://example.org')
print(js('document.title'))
PY
```

Reuse the current tab across commands and close task tabs when done. Browser
profiles persist across recreation. Only log into sites the owner authorizes.
Uploads/downloads should use the explicit `/state/...` container path; the same
host file lives under `/data/apps/browser/...`. No automatic vault injection.

### Whole-task delegation

```bash
printf '%s\n' 'Open https://example.com and report its heading. Read only.' | browser-use task
# Hermes: pipe the task to browser-use-hermes task
```

`task.py` starts a fresh task browser/profile, uses the official Python Agent,
limits it to **20 model turns / 180 seconds**, saves a result under
`/state/tasks/task-*/result.json`, and terminates the task browser/removes its
temporary profile in `finally`. Output files and run traces remain private;
they can contain page data. A completion verdict is model-reported: independently
verify important submissions. Do not retry ambiguous external writes blindly.

The configured model reuses the owner's existing Hermes OpenCode Go provider,
not Browser Use Cloud. The private `config/model.json` contains only the selected
model, compatible endpoint and its API key, mode0600. **Never print it or commit
it.** Refresh it deliberately when that provider credential/model changes. Go
requires an `x-opencode-session` header; task runs supply a unique task identifier.
Local browsers do not imply local model processing: page context is sent to
that configured remote model provider. No additional model account was created.

## Agent skills

Official `browser-use` and `open-source` skill directories were copied from the
recorded upstream revision into **only**:

- `~/.config/opencode/skills/{browser-use,open-source}`
- `~/.hermes/skills/{browser-use,open-source}`

Each SKILL.md retains its upstream body and adds a local-runtime preamble that
overrides host installation/cloud/MCP examples and selects the right launcher.
For recovery, check out the exact revision in upstream.json and run
`python3 infrastructure/browser/install-skills.py /path/to/checkout`. This only
creates absent skills; it preserves any existing user-modified copies.
Do not run the upstream unscoped installer: it would target excluded agents.
Do not upload these environment-bound skills to OpenViking. They are local
runtime integrations. No plugin is required. Newly discovered skills are
available in OpenCode; existing Hermes turns may need a new turn/session to
refresh their skill listing. No active serving agent process is restarted.

## Build, deploy and recover

```bash
docker build --network=host -t l3b-browser:1.0.0 infrastructure/browser
python3 infrastructure/l3b/portainer-api.py deploy --name browser --file infrastructure/l3b/browser.compose.yaml
install -m 755 infrastructure/browser/launcher.py ~/.local/bin/browser-use
# Create ~/.local/bin/browser-use-hermes -> browser-use only when absent.
python3 infrastructure/agents/check-integrations.py --single-node --memory
```

Build networking uses the host resolver because the retired default bridge is
disabled. This affects image construction only; the deployed container uses
`l3b`. Do not recreate the superseded bridge or add manual firewall rules.
Prepare `/data/apps/browser` and config directory mode0700 owned1000 before
deploying. Restore the model credential through the protected store, never Git.
Recover through Portainer; don't start an unmanaged duplicate runtime.

Initial setup corrected root-owned source-directory permissions, an undersized
PID ceiling and stale Chrome profile locks. These fixes are now in the tracked
image/runtime/compose sources. Keep the verification record honest about failed
and successful acceptance checks; no host-reboot acceptance is implied.

## Verified acceptance

- Direct navigation through both agent launchers returned the page title.
- The same origin's localStorage was different in each agent profile.
- Restarting the named container preserved both profile markers and recovered
  CLI connections; both internal CDP endpoints passed their readiness check.
- A delegated model run completed and returned inspected page content. The first
  request was rejected for a missing Go session header; the corrected runner
  supplies it. No extra model/browser-cloud subscription was added.
- A second delegated run filled and submitted a disposable loopback-only form;
  its local HTTP server independently received the exact expected name/email.
- Direct file upload (DOM.setFileInputFiles), actual download contents and a
  valid PNG screenshot were verified against a local disposable page.
- OpenCode loaded the scoped skill; `hermes skills list` reports both skills
  enabled. The scoped agent integration checker passes. These checks do not
  claim a separate end-to-end conversational model turn in each agent.
- No browser ports published, no Docker socket or full vault/auth mounted.

The image was deliberately redeployed during acceptance. Final image identity,
health and limits are recorded in `VERIFICATION.json`; no host reboot was done.

Playwright CLI remains installed for deterministic automation and regression
checks. AGENTS.md now explicitly permits this Browser Use runtime alongside it;
unrelated browser MCPs remain forbidden.
