# l3b core services — 2 November 2026

Current target: **one Debian host**, with the core applications managed through
Portainer stacks. OpenCode and the separately completed WireGuard installation
remain **host-native**. Historical Proxmox/VM/LXC instructions are not deployment
instructions for this node.

Read the [setup/WireGuard handoff](HANDOFF-2026-11-02.md),
[restore checkpoint](RESTORE-STATUS.md) and
[live acceptance record](CORE-VERIFICATION-2026-11-02.json) together.

## Network plan — owner correction, 2 November 2026

- LAN: **10.1.1.0/24**, host unchanged at 10.1.1.10.
- WireGuard peers: **10.1.2.0/24**, gateway unchanged at 10.1.2.1.
- Docker custom bridge **`l3b`**: **10.1.3.0/24**, gateway **10.1.3.1**.

The original 172.17.0.0/16 network was recreated in a scoped maintenance window;
all ten existing containers and service/identity proxy aliases were retained.
No volumes or identities were replaced. The bridge interface ID changes on
recreation; scripts must use the network name, not a hard-coded `br-*` name.
Reproducible creation for a new empty host:

```bash
docker network create --driver bridge --subnet 10.1.3.0/24 --gateway 10.1.3.1 l3b
```

All Compose sources continue to reference the external network by name. The
one-time [`migrate-network.py`](migrate-network.py) is guarded to the original
subnet and is **not** a recurring/startup job. It stops/reattaches the existing
containers for network maintenance; subsequent service definition changes use
Portainer. Identity, proxy and dashboard definitions were redeployed through
Portainer to update effective trust/host aliases. AdGuard/Unbound ACLs and the
stopped Hermes trusted-proxy setting use the new subnet. Existing historical
logs/backups were not rewritten.

[`verify-network.py`](verify-network.py) checks actual endpoints, aliases,
gateway, live trust settings, upstream host aliases and unchanged LAN/VPN routes;
see [network evidence](NETWORK-VERIFICATION-2026-11-02.json). Core DNS/TLS/auth,
memory and both browser MCPs passed after reconnection. Docker's later daemon
restart with live-restore passed during DNS setup; no reboot or independent
VPN-client test is claimed.

Native OpenCode's separate handover is now verified: it listens only on
**10.1.3.1:4096**, and Caddy serves the working private HTTPS origin. The previous
HTTPS502 is resolved. DNS defaults, WireGuard profiles and private/public policy
are applied and tested; see [DNS policy](DNS-POLICY.md) and
[native handover evidence](NATIVE-HANDOVER-2026-11-02.json).

## Deployed core

| Service | Placement / definition | Access |
| --- | --- | --- |
| Portainer BE 2.45.3 | `portainer` bootstrap; [Compose](portainer.compose.yaml) | `https://portainer.l3b.cc.cd`; internal `portainer:9000` |
| AdGuard Home 0.107.79 | Portainer `dns`, ID169; [stack](dns.compose.yaml) | Host **53/UDP only**; UI `adguard:3000` through `https://dns.l3b.cc.cd` |
| Unbound 1.26.2 | Same `dns` stack | Internal `unbound:5335`; no host port |
| Caddy 2.11.4 + saved custom plugins | Portainer `proxy`, ID171; [stack](proxy.compose.yaml) | Host **443/TCP and 443/UDP only** |
| Pocket ID 2.16.0 | Portainer `identity`, ID170; [stack](identity.compose.yaml) | Internal `pocketid:1411`; `https://auth.l3b.cc.cd` |
| Tinyauth 5.2.0 | Same `identity` stack | Internal `tinyauth:3000`; `https://login.l3b.cc.cd` |
| Homepage 2.4.0 | Portainer `dashboard`, ID172; [stack](dashboard.compose.yaml) | Internal `homepage:3000`; `https://l3b.cc.cd` behind Tinyauth |
| OpenViking 0.4.22 / Ollama 0.34.4 | Portainer `memory`, ID174; [stack](memory.compose.yaml) | Internal `openviking:1933` / `ollama:11434`; `https://memory.l3b.cc.cd` |

All application containers use the existing external Docker network `l3b` and
service-name upstreams. **There are no published Portainer, UI, MCP, CDP, HTTP80
or TCP53 ports**, including loopback publications. Image `EXPOSE` metadata shown
by `docker ps` is not a host publication. Only the `PortBindings`/live listeners
establish exposure.

Host-native SSH22, private OpenCode4096 and WireGuard UDP51820 are separate,
previously approved services. The owner subsequently authorized the native
`oc` HTTPS route and explicitly chose the prior vault password. Its
[one-shot service handover](REMOTE-ACCESS.md) preserves history and binds only
to the Docker bridge; it does not use the removed host proxy or a second server.
`hermes` HTTPS remains absent. The completion record, not this desired-source
description, determines whether native remote activation has passed.

The owner retired Tailscale on 2 November. No package, daemon or container is
installed on this node; no tailnet enrollment, remote-node removal or identity
deletion was attempted. WireGuard is the current VPN. Historical Tailscale
instructions are not deployment instructions.

## Dashboard

Homepage runs at the existing apex with the restored exact-owner/group Tinyauth
policy. The [current configuration](homepage/) preserves the neutral automatic
light/dark theme. It shows AdGuard Home (live DNS statistics), Portainer and
Pocket ID, each with a real service-name HTTP monitor. OpenViking/OpenCode cards
are now active after the verified native-service handover, for five live cards.
Desktop/light and mobile/dark tests passed. Retired cluster cards, Kubernetes metrics and stopped Hermes
are deliberately absent. No Docker socket, privileged widget or host port was
added. AdGuard credentials stay in the private runtime environment/Portainer
stack values; the browser receives the widget results, not those credentials.

Configuration persists at `/data/apps/homepage/config`. Homepage runs as UID1000
with capabilities dropped and no-new-privileges. Unlike the core daemons, its
image-owned runtime filesystem is writable because Next.js must regenerate
`/app/.next/server/pages` for settings/custom-theme changes. A read-only trial
left the default theme/title cached; it was corrected before acceptance.

The apex hostname in `/etc/hosts` was corrected from loopback to the host's
existing LAN address; DNS already answered correctly. The allowlisted Docker
hostname is `homepage:3000`, not a wildcard. The Caddy config was restarted
through Portainer after replacement of its bind-mounted source inode; future
edits should preserve that inode and use Caddy reload.

```bash
sudo python3 infrastructure/l3b/portainer-api.py deploy --name dashboard \
  --file infrastructure/l3b/dashboard.compose.yaml
python3 infrastructure/l3b/verify-homepage.py
```

[Browser acceptance](HOMEPAGE-VERIFICATION-2026-11-02.json) verifies desktop/light
and mobile/dark, the current card count, no overflow or console errors, and no
widget error panel. The HTTPS gate rejects anonymous/spoofed requests. Actual
human passkey/OIDC completion remains separate: UI rendering was tested inside
the Docker network, not by bypassing or weakening public authentication.

## Images, bootstrap and management

Compose files pin immutable published-image digests. AdGuard0.107.79 was checked
against its official current stable release. Unbound uses the maintained,
community-published **`klutchell/unbound:1.26.2`** distroless image, not a locally
built image and not the old saved ARM-targeted `mvance/unbound-rpi` definition.
Caddy uses the published official image with the already compiled, static
custom binary mounted read-only; Cloudflare DNS and the existing layer4 modules
were verified. No custom application Dockerfile remains.

Portainer is the bootstrap prerequisite, not a stack it should recreate through
its own running API process. Its single server uses the dedicated
`portainer` Compose project and existing `/data/apps/portainer` state.
It has no published API port. This is the only bootstrap/maintenance exception;
the application stacks above and the browser-tool stack are managed by
Portainer's API. No second Portainer server is running.

The initial saved Compose environment pointed at2.45.1, whereas the backup's
actual running-container manifest identified2.45.3. The older reader rejected
the schema; it was stopped, and the matching saved runtime digest was used.
No database reset or downgrade was performed. A failed self-management entry
created during setup was removed through the native API after moving the
bootstrap container to its distinct project; no Portainer DB editing was used.

Thirty saved legacy stack definitions remain available as recovery material.
They were **not** blindly redeployed. Their saved status is not evidence those
applications exist on this host. Only the current core stacks were accepted.

Normal management from this node:

```bash
python3 infrastructure/l3b/portainer-api.py status
python3 infrastructure/l3b/portainer-api.py deploy --name dns \
  --file infrastructure/l3b/dns.compose.yaml --env L3B_BIND_IP=10.1.1.10
sudo python3 infrastructure/l3b/portainer-api.py deploy --name proxy \
  --file infrastructure/l3b/proxy.compose.yaml --env L3B_BIND_IP=10.1.1.10
sudo python3 infrastructure/l3b/portainer-api.py deploy --name identity \
  --file infrastructure/l3b/identity.compose.yaml
```

The helper authenticates through the scoped HomeLab service account, calls
`https://portainer.l3b.cc.cd`, and waits for **actual native deployment completion**.
An initial status3 means deploying, not success. `sudo` is needed only to read
protected root-owned runtime environment sources; credentials are not printed.
It converts host `env_file` sources into Portainer environment references and
protected stack `Env` values, because Portainer cannot read arbitrary host paths.
Do not paste expanded stack environments into Git, output or shared memory.

If rebuilding from zero, Portainer must be bootstrapped first, then reached by
an authenticated client on the Docker network at `portainer:9000` to install
DNS/Caddy. Do not re-open permanent management ports as a shortcut. The HTTPS
helper's normal endpoint requires the DNS/proxy foundation to be operational.

## Persistent data and credentials

| Host path | Purpose |
| --- | --- |
| `/data/apps/portainer` | Original users, DB/key material, saved stack definitions |
| `/data/apps/adguard/conf`, `work` | AdGuard configuration, filters and application data |
| `/data/apps/unbound/unbound.conf`, `state` | Reviewed resolver configuration and persistent DNSSEC trust anchor |
| `/data/apps/caddy/caddy`, `Caddyfile`, `data`, `config` | Custom binary, routes, original certificate/account storage, runtime config |
| `/data/apps/pocket-id/data`, `encryption-key` | Original identity database/uploads and matching encryption key |
| `/data/apps/tinyauth/data` | Original SQLite data and resources |

`/data` is the UUID-mounted Seagate XFS filesystem. Docker-managed images,
runtime and named volumes remain on Samsung NVMe. These are bind mounts, not a
Docker data-root relocation. Docker retains its existing storage dependency on
the actual `/data` mount.

Runtime `.env` sources and keys stay outside Git with private permissions.
Portainer/Caddy state remains root-managed; Pocket ID/Tinyauth and Unbound run
with explicit non-root UIDs. Application roots are read-only, capabilities are
dropped except AdGuard/Caddy's low-port capability, and privilege escalation is
disabled. Writable application state is limited to declared mounts/tmpfs.

The one-shot [core staging script](prepare-core.py) records how selected cold
application files were copied from the backup's preferred final paths. **Do not
rerun it over a production directory.** It refuses existing destinations by
default and refuses interrupted-staging resume while a core service is running.
Resume is for the same reviewed interrupted first copy, not a deployment method.

The external HOMELAB_BACKUP remains temporarily mounted at
`/mnt/HOMELAB_BACKUP`, UUID `c05e9f2d-a64e-4012-9407-a3dc94475dbb`, without fstab
persistence. Its files were read only; no formatting, repair, restore over its
contents, recursive permission change or unmount occurred. This is not proof of
a current-node backup. Portainer's restored UI also carries an old failed-backup
notice; backup scheduling/recovery coverage needs its own reviewed task.

## DNS, TLS and identity policy

- AdGuard sends ordinary queries only to `unbound:5335`, with no public fallback.
  Docker DNS resolves that service name. Unbound performs recursion and DNSSEC
  validation; invalid signatures return SERVFAIL.
- Unbound uses two workers,32MiB message/64MiB RRset caches, prefetch, minimized
  responses/QNAMEs and a1232-byte EDNS buffer. AdGuard's restored128MiB cache,
  optimistic caching, DNSSEC request policy and100-query rate limit were retained;
  no universal performance advantage or workload benchmark is claimed.
- Only UDP53 is published by owner choice. Oversized/truncated client replies
  have **no TCP fallback** on the host. Unbound may still use TCP for upstream
  recursion. AdGuard DoH/DoT listeners are disabled.
- Host resolver is now only `10.1.1.10`. The parallel config snapshot records it.
  Router/client DNS settings and the working WireGuard profiles remain unchanged;
  those profiles still use1.1.1.1.
- Private zone answers target this node. Cloudflare apex and explicit `oc` A
  records were changed from the retired proxy to this node; other records,
  including the new `wg` record and existing public exceptions, were preserved.
- Caddy DNS-01 uses the saved Cloudflare token and certificate/account storage.
  No HTTP80 listener or redirect is enabled. Public DNS does not by itself
  expose an application; the core routes retain LAN/WireGuard source controls.
- The routed WireGuard subnet is included in Caddy and AdGuard access rules,
  because source NAT is intentionally absent. No WireGuard key/profile/firewall
  changes were made. Its iPhone acceptance record remains authoritative.
- Pocket ID retains its original encryption key, one user and18 OIDC clients.
  `auth.l3b.cc.cd`/`login.l3b.cc.cd` are Docker network aliases for Caddy, so
  server-side OAuth requests also use the real HTTPS origins.
- Portainer retains native OAuth and its existing local-admin fallback. Tinyauth
  retains deny-by-default owner/group ACLs; AdGuard UI requires forward-auth.
  An unauthenticated request, including spoofed identity headers, returns401.

## Agent boundary and deferred work

OpenCode remains the existing native host process. Its current authentication,
sessions and Herdr integration were preserved. Skills and selected MCP settings
were restored; Codex/Claude configuration was excluded explicitly.

The Portainer-managed [tools stack](tools.compose.yaml), ID173,
provides one shared Chromium process. Host Playwright and Chrome DevTools use
Docker exec/stdio, without MCP/CDP host publications. Hermes's prepared clients
use Docker service discovery internally. Context7, shadcn and REA also connect;
unrestored-service MCPs remain disabled. This is a privileged browser tool, not
an isolation boundary. No owner profile/session was imported into the browser.

Browser MCP permission repair: the running user manager predated `dev`'s Docker
group membership. Both native browser MCP launches now explicitly select that
already-authorized group with `sg docker -c`, retaining the host dev UID, without socket chmod,
extra ports or another browser. Actual tool calls pass; see
[browser verification](BROWSER-VERIFICATION-2026-11-02.json). The native unit and
detached handover launcher use the same selection and preflight Docker access.
Agent Browser was researched as an optional CLI/MCP alternative, not installed.

Owner naming standard: generic, single-word stack names; actual, single-word
service/container names. Containers are `portainer`, `adguard`, `unbound`,
`caddy`, `pocketid`, `tinyauth`, `homepage`, `playwright`, `openviking`, and
`ollama`. `hermes` stays
stopped. Portainer compose stack names cannot be updated in place: the five
old managed records were replaced through the native API, reusing all bind data
and the external network. Old IDs162–165/168 are historical. Application data
directories, domains and container credentials/identities were not renamed or reset.

Hermes configuration/persona/skills were staged but its stack166 is stopped.
No old conversation DB, cron jobs, process locks or messaging gateway was
restored into active execution. Complete Hermes/model/messaging acceptance only
after the owner accepts the core. Telegram/Tavily rotation warnings remain deferred.
OpenViking has now been restored and verified; see [memory](MEMORY.md) for the
official plugin, three skills and explicitly chosen automatic capture. The temporary duplicate
OpenCode Docker server, its unused data/images and the unwanted host proxy were
removed; none remains in the desired stack files.

## Verification

```bash
python3 infrastructure/l3b/verify-core.py --browser
python3 infrastructure/l3b/verify-homepage.py
python3 infrastructure/l3b/verify-memory.py
python3 infrastructure/agents/check-integrations.py --single-node --memory
```

The browser option checks an actual signed-in Portainer administrator session
and Secure/HttpOnly/Strict cookie attributes, without reading or printing keys.
The saved acceptance JSON records UDP DNS, valid/invalid DNSSEC, trusted TLS and
HTTP2, identity discovery/JWKS, auth bypass rejection, exact Docker port bindings,
mount identities, container hardening and preservation of the WireGuard service.

Human passkey/OIDC completion, remote client application requests, independent
HTTP3 transport testing, reboot/Docker-daemon restart and new backup/restore
coverage remain distinct acceptance items. No paid agent model request or
unrelated application restore was used to claim the initial core success.
