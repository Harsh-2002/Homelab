# Host-native WireGuard on l3b

## Current acceptance — 2 November 2026

The owner reports WireGuard working. The [live verification record](VERIFICATION-2026-11-02.json)
confirms an iPhone handshake and bidirectional traffic, active/enabled service
and matching saved/running peer state. MacBook has not connected in that
snapshot. The corrected router /24 route and UDP forward are shown in the
owner's screenshots. This supersedes historical pending-first-client language
below; cold boot, actual Docker restart and separate MacBook testing remain
distinct checks. The exact remote network/LAN targets were not independently
observed.

For continuation, read [the current handoff](../HANDOFF-2026-11-02.md) and
[configuration index](../config/README.md). Root-only live WireGuard state is
excluded from Git; key-free server/client examples are provided beside this
runbook. Client Documents remain **MacBook** and **iPhone** in HomeLab.


Deployed 1 November 2026. WireGuard runs on the Debian host, not Docker.
The kernel data path uses the existing signed Debian kernel; the Debian
`wireguard-tools` package is `1.0.20210914-3`.

## Configuration

| Setting | Value |
| --- | --- |
| Service | `wg-quick@wg0`, enabled and active |
| Tunnel | `wg0`, `10.1.2.1/24` |
| Clients | Unique `/32` addresses, `10.1.2.2` through `10.1.2.254` |
| Listen port | UDP 51820 |
| Endpoint | `wg.l3b.cc.cd:51820` |
| Client routes | `10.1.1.0/24`, `10.1.2.0/24` |
| Client DNS | `1.1.1.1` pending the owner's DNS deployment |
| LAN mode | Routed; no VPN-to-LAN masquerading |
| First retained profile | `macbook`, `10.1.2.2/32` |
| MTU | wg-quick automatic selection |
| Roaming-client keepalive | 25 seconds |

This is split-tunnel access. General internet traffic, including the current
public DNS resolver, remains on the client's normal connection. WireGuard does
not distribute DNS settings dynamically to already imported profiles; update
and re-import them after changing DNS. Client profile routes do not override
server firewall restrictions. VPN client-to-client forwarding and arbitrary
internet forwarding are denied. Authenticated clients can access host services;
there is no per-service authorization inside the tunnel beyond normal service
authentication and the existing host firewall.

## Router and DNS prerequisites

The owner's TP-Link screenshot exposes the required IPv4 Static Routing page.
Add an enabled route, selecting LAN if an interface is requested:

| Field | Value |
| --- | --- |
| Network destination | `10.1.2.0` |
| Subnet mask | `255.255.255.0` |
| Gateway | `10.1.1.10` |

This is the return route for LAN replies to the VPN subnet. LAN hosts must use
that router or an equivalent correct route. Their local firewalls may also need
to permit the VPN subnet. Routed access preserves client source addresses and
avoids source translation; no measured speed advantage over scoped NAT is
claimed.

Separately forward **UDP 51820 to 10.1.1.10:51820** on the router. This does not
replace the static route. Point `wg.l3b.cc.cd` at the reachable home public IP,
with **DNS-only** mode, not an ordinary Cloudflare HTTP proxy. At the initial
deployment check this name resolved through an existing wildcard to the old
private address `10.1.1.3`; external endpoint resolution still needed correction.
CGNAT/double-NAT/public reachability was not established by a local handshake.
Do not advertise an untested AAAA record. A changing public IP requires a
separately configured update mechanism; none was silently added here.

## One firewall backend

Live `iptables --version` reports `nf_tables`. Debian's iptables alternatives
select `iptables-nft`. These commands program nftables kernel rules; this is not
a second independent active firewall alongside nftables. Legacy-save output had
no rules, and standalone `nftables.service` was disabled. We retained that state
and did not switch Docker to its separate native nftables backend, remove
firewall packages, flush the ruleset or disable Docker's firewall handling.

The existing `net.ipv4.ip_forward=1` is persistent in
`/etc/sysctl.d/90-homelab.conf`. Docker retains FORWARD policy DROP.
`/usr/local/libexec/l3b-wg-firewall` manages only `L3B-WG` and its own jump/NAT
rule. It hooks DOCKER-USER when present, otherwise FORWARD:

- Allow VPN-subnet traffic from wg0 to the home LAN through eno1.
- Allow established/related return traffic to VPN clients.
- Return DNAT traffic toward Docker bridges to Docker's normal published-port
  rules; do not grant direct access to unpublished container ports.
- Drop other forwarded traffic entering/leaving wg0, including peer-to-peer.
- In routed mode, add no VPN source-NAT rule. Existing Docker NAT remains.

WireGuard PostUp/PostDown install/remove the rules. Docker's systemd drop-in
`/etc/systemd/system/docker.service.d/20-wireguard.conf` adds
`ExecStartPost=/usr/local/libexec/l3b-wg-firewall up` so a subsequent Docker start
reconciles the VPN hook. It exits harmlessly if wg0 is absent. The wg0 drop-in
`/etc/systemd/system/wg-quick@wg0.service.d/10-ordering.conf` orders it after
Docker at boot without requiring Docker to run the VPN. Docker was not restarted
for this setup; a later actual Docker restart/cold boot remains a persistence
acceptance check.

## Profile manager

Global entry point: `/usr/local/bin/wg.sh`. Root-owned Python manager:
`/usr/local/libexec/l3b-wg-manager`. The three non-secret source files beside
this runbook reproduce these installed scripts. Commands require sudo:

```bash
sudo wg.sh status
sudo wg.sh list
sudo wg.sh add iphone
sudo wg.sh verify iphone
sudo wg.sh export iphone
sudo wg.sh revoke iphone
```

`export` without --output intentionally writes the complete secret profile to
stdout. Use it only in the owner's terminal or redirect over SSH, never in an
agent transcript. A protected file export is also available:

```bash
sudo wg.sh export macbook --output /home/dev/macbook.conf
```

It refuses to overwrite an existing path, requires an absolute path whose parent
belongs to the invoking user, and creates a mode-600 file owned by that user.
Transfer the profile privately, import it into WireGuard, then remove the extra
export copy. Do not commit it. To download directly from the Mac without
displaying it, run this in the Mac terminal with a suitable new destination:

```bash
(umask 077; set -C; ssh dev@10.1.1.10 'sudo wg.sh export macbook' > "$HOME/Downloads/l3b-macbook.conf")
```

Each device gets a distinct private/public identity and preshared key. Names and
addresses are validated, duplicate profiles are rejected and changes use atomic
file replacement plus a root-only process lock. `wg syncconf` applies peer
changes without restarting existing tunnels. Verify checks key encoding,
derived public keys, unique addresses, saved profile content/permissions and
agreement with running server/peer/preshared-key state without printing secrets.
It does not claim a remote device has connected merely because configuration
validation passed.

Authoritative private state is `/etc/wireguard/l3b.json`, generated server
configuration `/etc/wireguard/wg0.conf`, and importable profiles
`/etc/wireguard/clients/NAME.conf`. Directories are root-owned 700 and files 600.
These contain secrets and are not tracked. The helper retains client private
keys to support later export; root and passwordless-sudo dev can access them.
Revoke removes saved and live authorization plus the server's retained client
profile, but cannot erase copies previously exported elsewhere. Deleting all
private state would destroy the existing tunnel identities; never rerun init
or regenerate keys to solve an unrelated problem. `init` refuses existing state.

Change future/exported profile DNS or the endpoint with:

```bash
sudo wg.sh configure --dns 10.1.1.10
sudo wg.sh configure --endpoint wg.l3b.cc.cd
```

The DNS address above is an example: only select it once the intended DNS
service is deployed and reachable. Re-export/re-import existing client profiles.
If a router cannot supply the return route, an explicit fallback is:

```bash
sudo wg.sh configure --mode nat
```

That enables masquerading only for VPN-subnet-to-LAN traffic, not all traffic.
Restore the selected routed design with `sudo wg.sh configure --mode routed`.

## Tests and remaining acceptance

Passed during deployment:

- Real kernel WireGuard handshake between the host and a temporary network
  namespace client, with separate generated identity and PSK.
- Encrypted ping to 10.1.2.1 and an actual SSH protocol response across the tunnel.
- Consistent saved/running keys and peers; temporary peer removed live and on disk.
- Protected export to dev:dev mode 600, then export file removed.
- Repeated firewall reconciliation produced one hook rather than duplicate rules.
- No general internet forwarding through the gateway under this split-tunnel policy.
- Service active/enabled, UDP listener present, scripts parse and manager verifies.
- Existing containers remained running; none restarted by the WireGuard setup.

The temporary client, namespace, veth links, export and test script were removed.
No kernel/disk changes or host reboot were performed for WireGuard.

Routed gateway ping did **not** receive a reply during the initial test; the
router return route was not verified then. Test after the owner adds it. Internet
handshake, public DNS/public-IP correctness, router port-forwarding, client app
import, useful remote LAN/application requests and a cold boot remain explicit
acceptance items. A working local tunnel does not prove internet reachability.

## Sources

- [WireGuard quick start](https://www.wireguard.com/quickstart/)
- [Docker iptables integration](https://docs.docker.com/engine/network/firewall-iptables/)

The owner reported the Tailscale account deleted. No Tailscale CLI was found on
this new node. Historical repository references remain history; they were not
globally rewritten to claim the retired cluster now runs WireGuard.

### Public endpoint completed

After installing and authenticating the official Cloudflare CLI as dev, created
an explicit DNS-only A record for wg.l3b.cc.cd with a 300-second TTL, using the
node's observed public egress IPv4 address. Cloudflare API readback, host
resolution and Google's public DNS resolver confirmed the correct result.
This supersedes the initial wildcard/private-address prerequisite above.
The record is not dynamic DNS; update it if the home public address changes.
Router port-forward/static-route and actual internet-client acceptance remain
pending. No public IPv4 address is embedded in the architecture inventory.

### Cloudflare CLI for dev

Official cf 1.0.0-beta.26 is installed through npm in /home/dev/.local,
with cf and cloudflare commands. Headless device OAuth completed successfully;
cf auth whoami confirmed a valid login, zone discovery found l3b.cc.cd active,
and actual DNS record creation/readback succeeded. Requested scopes are
account:read, zone.read, dns.read, dns.write and user-details.read; the CLI
also granted offline_access. Credentials are in dev's protected
~/.config/cloudflare/config/default.json, mode 600 under a mode-700 parent
tree. Do not print, copy into Git, or include this file in agent transcripts.

Use cf auth whoami, cf auth scopes dns, and
cf dns records list --zone l3b.cc.cd for non-secret verification.
Future sign-in uses cf auth login --no-browser as dev. Update the user-local
CLI with npm install --global --prefix /home/dev/.local cf@latest.
OAuth access-token expiry is displayed by the CLI; offline_access enables its
refresh mechanism, but a future unattended refresh was not independently tested.
The optional workerd install script was blocked by npm's existing script policy;
the DNS/auth API functionality used here works and was verified. Local Worker
simulation was not requested or configured.

### Router WAN identity confirmed

The owner supplied a TP-Link status screenshot showing WAN interface
pppoe_gpon_799_1 with the same public IPv4 address used in the new DNS record.
The static route must use LAN, because its next hop is the Debian LAN address.
The separate inbound UDP forward must use the active PPPoE WAN interface.
This confirms the displayed WAN/public-IP match; successful inbound handshake
still requires the actual enabled port-forward rule and a remote client test.

## Device profiles saved in HomeLab — 2 November 2026

Two distinct active peers have downloadable 1Password Document items in the
owner's HomeLab vault:

| Document title | Download filename | Peer | VPN address |
| --- | --- | --- | --- |
| MacBook | MacBook.conf | macbook | 10.1.2.2/32 |
| iPhone | iPhone.conf | iphone | 10.1.2.3/32 |

Each device has separate keys and a preshared key. Both profiles passed manager
verification, then were streamed directly into the scoped service-account
document API. Private download/readback matched the generated configuration
byte for byte. No temporary profile files or key contents were exposed.
The first MacBook upload was renamed to the requested simple title; no extra
long-title copy remains. Existing unrelated vault documents were preserved.

The endpoint is wg.l3b.cc.cd:51820 with split routes for the home LAN and VPN
subnet; client DNS remains 1.1.1.1 as requested. The owner supplied screenshots
showing the corrected /24 router route and enabled UDP forwarding. Successful
internet-client connection and real LAN access remain pending the owner's app
import/test. Test the iPhone on cellular with Wi-Fi off to exercise inbound
router forwarding rather than only a local connection.

The upload encountered an unreachable IPv6 destination during one request.
A retry using a per-process system-resolver setting succeeded; no permanent
DNS, firewall or IPv6 policy was changed by this profile-storage task.
Do not infer a proven general DNS root cause from that retry.
