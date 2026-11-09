# Home Assistant OS

New gaming-PC smart plug (2026-11-09): candidate discovered and current address
reserved without power interruption. Local-key/account approval and telemetry
integration remain pending. **Never toggle/reset this plug during testing.**
See [WIPRO-PLUG-LOCAL.md](WIPRO-PLUG-LOCAL.md).

> **2026-11-02:** The active deployment is the Docker/Portainer stack on l3b:
> [`infrastructure/l3b/homeassistant.compose.yaml`](../l3b/homeassistant.compose.yaml).
> Private URL: `https://home.l3b.cc.cd`; data: `/data/apps/homeassistant`.
> HAOS add-ons Mosquitto and SSH were not restored. MQTT now runs as the
> `mqtt` Docker stack and Frigate camera/sensors are working; the Tuya bulb
> (10.1.1.241) and Samsung AC (10.1.1.233) are working after DHCP reassignment.
> VictoriaMetrics/Grafana are retired; Beszel is the
> monitoring stack and the Nodes view links to it. The HAOS/Proxmox details
> below are historical.

Frigate and node monitoring (2026-10-22): **Homelab** sidebar dashboard has
[Cameras](https://home.l3b.cc.cd/homelab-status/cameras) and
[Nodes](https://home.l3b.cc.cd/homelab-status/nodes). Authenticated MQTT and RTSP,
GPU H.264 compatibility restream, working browser playback,27 physical-host
metrics from existing VictoriaMetrics. px10 exporter startup race repaired on
all hosts. Latest owner preference: no explanatory paragraphs in Nodes/Cameras/
AC Care, clear labels and confirmation-protected compact maintenance tiles.
See [FRIGATE-AND-NODES.md](FRIGATE-AND-NODES.md) for reproduction and rollback.

Samsung AC dashboard (2026-10-22): separate native **Control** and **Care** at
`/samsung-ac/control` and `/samsung-ac/care`. Independent airflow, comfort,
five-step cooling, local schedule and honest care/history coverage. Schedule
and alerts initially disabled. Live reads/rendering and safety rejection tests
passed; physical write/outage acceptance remains pending. Reproducible source,
patches and rollback: [SAMSUNG-AC-DASHBOARD.md](SAMSUNG-AC-DASHBOARD.md).

Samsung AC **AR50H18D14HNNA** local integration (2026-10-22): device10.1.1.233 (originally .241; DHCP moved),
MAC34:55:E5:0A:80:D7, authenticated OCF/CoAP over DTLS UDP49154. LocalThings
releasev0.34.0 installed on Core2026.10.2 after native backup0b406e2d. Native
**climate.samsung_room_ac** is loaded with live state, fan/modes/presets/swing;
private HTTPS read and integration reload verified, no actuator or WAN-outage
test yet. Credentials concealed HomeLab/Samsung AC - Room. See
[SAMSUNG-AC-LOCAL.md](SAMSUNG-AC-LOCAL.md) for evidence, model/software reference,
installation, acceptance boundaries and rollback. Keep SmartThings registration.

Wipro/Smart Life bulb local-control investigation (2026-10-22): verified
10.1.1.241↔10:5A:17:51:D7:9D (originally .231), encrypted Tuya3.3 LAN announcements, port6668.
REA packet evidence and preparation in [BULB-LOCAL.md](BULB-LOCAL.md). Tuya
Local2026.9.2 installed after native backup a8059954; config check/Core restart
passed. Owner Smart Life approval completed; **light.behind_monitor_bulb** now
works through Tuya Local with tested LAN power/brightness/colour/white control,
restored to its prior visible on/white setting. Local key concealed in HomeLab
Wipro Bulb - Behind Monitor. Actual WAN-outage validation remains untested.
No firmware/reset/router changes. See the bulb runbook for API access/evidence.

Home Assistant OS 18.3 is installed as Proxmox VM 107 (`haos`) on px30. The official `haos_ova-18.3.qcow2.xz` KVM image was downloaded directly on px30, checked against the release's SHA-256 digest, decompressed, validated with `qemu-img check`, and imported to `local-zfs:vm-107-disk-1`. The source download and QCOW2 staging directory were removed after the independent ZFS disk was verified.

Current VM configuration: OVMF with the `4m` EFI vars type and no pre-enrolled Secure Boot keys, one socket with two vCPUs, fixed 4 GiB RAM (`balloon: 0`), VirtIO NIC on `vmbr0`, VirtIO SCSI single controller, `scsi0` on local-zfs with discard, SSD and I/O thread enabled, and boot order `scsi0`. The imported disk was expanded from its 32 GiB image default to **40 GiB** at the owner's request; Proxmox reports the ZFS zvol at 40 GiB. Home Assistant OS can expand its guest data partition after a boot with the larger disk. The empty virtual CD-ROM was removed. VM 107 was started and is running on px30.

The owner has no physical Zigbee, Thread, Z-Wave or other radio passthrough planned. Home Assistant OS in a dedicated VM was chosen over Home Assistant Container because the supported HAOS/Supervisor installation manages its own core, OS and apps and preserves the option to move the VM between nodes. No VM boot ISO is needed; HAOS is imported as a prepared KVM disk.

## Access and availability

The official Terminal & SSH app (`core_ssh` 10.5.0) is installed with the `dev` VM's Ed25519 public key, no SSH password, and host port 22. It starts on boot. From `dev`, use `ssh haos` (alias in `/home/dev/.ssh/config`); this opens the app container and its Home Assistant CLI/config mount, not the underlying HAOS host filesystem. A key-only `ha core info` call succeeded. The QEMU guest agent is already included in the HAOS image: `qm guest cmd 107 ping` and `qm guest exec 107` work, and the `qemu-ga` process is running. Do not attempt Alpine package management on the HAOS host: HAOS is a Buildroot-generated appliance, while its SSH app container is Alpine-based.
VM 107 was rebooted after setup. SSH returned with the app in `started`/`auto` state, `ha core info` reported Core 2026.9.4, the Caddy URL returned HTTP 200, and the QEMU guest-agent command channel continued to work. Homepage's native Home Assistant widget showed live counts after this reboot.

- LAN IP: `10.1.1.13/24` (static, gateway `10.1.1.1`). HAOS initially received temporary DHCP address `10.1.1.231`; after the owner configured its static address, the UI responded at `http://10.1.1.13/` on 2026-09-29. Port 8123 redirects to port 80 on this image. Port 4357 is only the HAOS Observer page, not the setup UI; it reported Supervisor connected, supported and healthy.
- The owner completed initial onboarding and created an account. The Proxmox QEMU guest agent responds to `qm guest cmd 107 ping`. In Home Assistant 2026.9, HTTP settings are managed under Settings > System > Network. Trust X-Forwarded-For is enabled there, with only Caddy `10.1.1.3/32` trusted. An initial `http:` YAML block was imported by Home Assistant, then removed because it was ignored after migration and raised a repair warning; do not add it back. The HA configuration check succeeded.
- Private HTTPS URL: `https://home.l3b.cc.cd`. The existing wildcard DNS resolves it to Caddy `10.1.1.3`, which proxies to `10.1.1.13:80`. Caddy applies the private LAN/Tailscale source policy, and Home Assistant retains its native login. No public Cloudflare record was created. Validated from `dev`: HTTPS root 200, unauthenticated `/api/` 401, WebSocket `/api/websocket` 101 with `auth_required`.
- Proxmox HA resource `vm:107` is started on px30. ZFS replication job `107-0` sends both VM disks from px30 to px20 every five minutes. The initial sync completed successfully on 2026-09-29, with zero failures and both disks verified on px20.
- Strict node-affinity rule `vm107-replica-nodes` prefers px30 and permits px20. HA must not choose px10 because it has no VM 107 replica. A real node-failure/failover test has not yet been performed. Replication is asynchronous, so up to the interval plus any replication lag may be lost in a sudden failure.
- The existing `critical-to-backup` job now includes VM 107. It runs daily at 02:00 to the `BACKUP` SMB storage, uses zstd snapshot backup and keeps the latest backup only. The first scheduled backup has not yet run. Backup is separate from replication and protects against deletion or bad configuration.

## Next steps

- Homepage now has a private card, direct health check, and native people/lights/switches widget. Its token is injected through the live `homepage-widgets` Kubernetes Secret. Do not create a public DNS record for this hostname.
- Hermes uses the long-lived Home Assistant token via `HASS_TOKEN` and the direct LAN URL via `HASS_URL` in its mode-0600 `.env`; the token is also in the existing `Home Assistant` HomeLab 1Password item. The owner supplied this token for both Hermes and Homepage. Never commit it.
- Home Assistant Core does not include a generic OIDC authentication provider. The community `hass-oidc-auth` integration supports Pocket ID with a public PKCE client and can preserve local login, but it is a third-party authentication extension. Do not mistake Home Assistant's OAuth2 integration credentials for inbound SSO. The native account remains the break-glass login until a separately verified OIDC installation and account-linking test.
- Test HA relocation to px20 during a planned maintenance window; do not force a host failure merely to validate it.

References: [Home Assistant Linux installation](https://www.home-assistant.io/installation/linux/), [Home Assistant authentication providers](https://www.home-assistant.io/docs/authentication/providers/), [Community OIDC integration and Pocket ID guide](https://github.com/christiaangoossens/hass-oidc-auth/blob/main/docs/provider-configurations/pocket-id.md), [Proxmox VM disk import](https://pve.proxmox.com/pve-docs/qm.html).

## 2026-11-06 Samsung AC unreachable after DHCP move

`climate.samsung_room_ac` went unavailable while the unit still worked in the
SmartThings app. Root cause: the router leased the AC a new address and the
Localthings config entry still pointed at the old one, which had been reassigned
to a phone.

```
device MAC   34:55:E5:0A:80:D7
old host     10.1.1.233   (now another device)
new host     10.1.1.236
port         49154
```

The entry host was changed to `10.1.1.236` with Home Assistant stopped (so
`.storage/core.config_entries` would not be overwritten on shutdown), then HA was
started. The entity returned with live data: state `off`, current 30 °C,
target 26 °C, modes off/auto/cool/dry/fan_only.

### Diagnostic trap worth remembering

A TCP port scan of the AC finds **nothing open**, and this is expected. Samsung
appliance local control is **DTLS over UDP** on 49154, not TCP. A plain CoAP GET
to that UDP port returns a 15-byte fatal DTLS alert
(`15 02 00 00 ... 02 02 28`), and an `openssl s_client -dtls1_2 -connect
<ip>:49154` completes far enough to present the Samsung OCF device certificate.
Use the UDP/DTLS probe, never a TCP scan, to decide whether the device is alive.

A DHCP reservation for `34:55:E5:0A:80:D7` is still outstanding; it needs the
TP-Link admin login at `10.1.1.1`.

## 2026-11-07 router reservations and DHCP DNS

Set on the TP-Link XC220-G3v (`10.1.1.1`) through the LAN Settings page, with
Playwright driving the UI because the login form is JS-encrypted:

| Device | MAC | Reserved |
| --- | --- | --- |
| Samsung AC | `34:55:E5:0A:80:D7` | `10.1.1.238` |
| Tuya bulb | `10:5A:17:51:D7:9D` | `10.1.1.239` |

DHCP server settings changed at the same time:

```text
Pool          10.1.1.230 - 10.1.1.249   (unchanged)
Lease         120 minutes                (unchanged)
Domain        l3b.cc.cd                  (unchanged)
Primary DNS   10.1.1.10  (AdGuard)       was 1.1.1.1
Secondary DNS 1.1.1.1    (Cloudflare)    was 1.1.1.2
```

Before this, DHCP handed every client Cloudflare directly, so LAN devices
bypassed AdGuard entirely. Now they use the internal resolver first and fall
back to Cloudflare only if AdGuard is down. The change applies at each client's
next lease renewal, not immediately.

Reservations take effect at the same renewal. The devices are still on `.236`
and `.241` until then, so the Home Assistant entries must not be changed until
the leases move.

## 2026-11-07 Home Assistant entries moved ahead of the leases

Because the reservations were already saved on the router, the Home Assistant
config entries were updated to the new addresses rather than left pointing at
the old ones:

| Entry | Before | After |
| --- | --- | --- |
| `localthings` (Samsung AC) | `10.1.1.236` | `10.1.1.238` |
| `tuya_local` (bulb) | `10.1.1.241` | `10.1.1.239` |

HA was stopped, `.storage/core.config_entries` edited, then started. It came back
healthy. The Tuya `local_key` and the Localthings certificates/`device_key` were
not touched — only the `host` fields changed.

**Temporarily, until the devices renewed:** both entities showed `unavailable`.

```text
climate.samsung_room_ac    unavailable
light.behind_monitor_bulb  unavailable
```

The device side is still on the old leases, so HA correctly cannot reach them.
This is expected, not a fault. The entries recover when the bulb is power-cycled
at the switch and the AC at the breaker, or when the 120-minute lease expires and
each device renews onto its reservation.

Verify after the devices move:

```sh
ip neigh show | grep -iE '34:55:e5|10:5a:17'      # expect .238 and .239
curl -s -H "Authorization: Bearer $HASS_TOKEN" \
  "$HASS_URL/api/states/climate.samsung_room_ac"   # expect a real state
```

A step-by-step revert, if ever needed, is the same edit in reverse: stop HA, set
the two `host` values back, start HA.

### Recovered

Both devices were power-cycled and renewed onto their reservations:

```text
10.1.1.238  lladdr 34:55:e5:0a:80:d7  REACHABLE   Samsung AC
10.1.1.239  lladdr 10:5a:17:51:d7:9d  REACHABLE   Tuya bulb
```

The AC answered the DTLS probe on UDP 49154 at its new address, and Home
Assistant came back with live state at 23:46 IST:

```text
climate.samsung_room_ac    dry   28.0 °C
light.behind_monitor_bulb  on
```

No `device unreachable` or Tuya `error 901` entries after that point. The router
now guarantees those two addresses, so this failure mode is closed unless a
device is replaced.

## 2026-11-08 Nodes dashboard replaced Proxmox with host sensors

The `homelab-status` dashboard's **Nodes** view previously just linked to Beszel
because the Proxmox sources were retired. It now shows live host data from the
`homelab-stats.service` endpoint (`10.1.3.1:8099`, see
[../l3b/host/README.md](../l3b/host/README.md)).

`packages/homelab_metrics.yaml` defines a REST integration polling that endpoint
every 15 seconds and exposing:

```text
sensor.host_cpu            sensor.host_containers      sensor.host_disk_root
sensor.host_memory         sensor.host_unhealthy       sensor.host_disk_data
sensor.host_memory_used    sensor.host_load            sensor.host_disk_backup
sensor.host_temperature    sensor.host_uptime_hours
```

`dashboards/homelab.yaml` renders them as three sections: host gauges (CPU, RAM,
temperature), disk gauges (root, data, backup) and a Docker entities card with a
link to Beszel for history and per-container detail.

Both files are tracked under `config/` for reproducibility; the live copies are
`/data/apps/homeassistant/packages/homelab_metrics.yaml` and
`/data/apps/homeassistant/dashboards/homelab.yaml`. Verified after restart: all
ten sensors report values (CPU 12.6 %, RAM 47.3 %, 61 °C, 39 containers, 0
unhealthy, root 73.7 %, data 19.6 %, backup 16.1 %).

## Cleanup 2026-11-09: orphaned Proxmox entities and dead notification

The Overview "Favourites" showed 27 `sensor.px10_*`, `sensor.px20_*` and
`sensor.px30_*` entities (platform `rest`) stuck as **Unavailable**. Their YAML
had already been removed, so they survived only as orphan entries in the entity
registry. With Home Assistant stopped:

- backed up `.storage/core.entity_registry` and `.storage/core.restore_state` to
  `*.bak-20261109`;
- removed the 27 px entities from the registry (55 -> 28);
- removed the dead `notify.mobile_app_anurags_iphone` action from the
  `l3b power-button event` automation. That service no longer exists (no
  mobile_app config entries), so every power-key event produced an error;
  `persistent_notification.create` remains and works;
- deleted the unused `/data/apps/homepage/config/proxmox.yaml` widget stub;
- `PRAGMA quick_check` on `home-assistant_v2.db` returned **ok**. The recorder's
  "was shutdown cleanly" warning is only the unclean-shutdown flag left by the
  power cuts, not corruption.

Home Assistant restarted healthy with no errors, and the px entities are gone
from both the registry and the UI. Beszel already tracked only l3b
(`10.1.1.10`), so no Proxmox monitoring remained there.

Older design notes (`FRIGATE-AND-NODES.md`, `HOMELAB-UI.md`,
`dashboard-direction.md`) still describe the retired px cluster; treat them as
history, not current state.

## 2026-11-09 power-loss corruption and recovery

The repeated hard power-offs corrupted `.storage/core.config_entries` at 08:14
(Home Assistant kept a 0-byte `core.config_entries.corrupt.2026-11-09T02:44:01`
marker). On restart the integration list was reset to the five defaults, the
device registry dropped to Sun/Backup, and 198 entities moved to
`deleted_entities` (frigate 52, localthings 35, mobile_app 32, hassio 28, upnp
17, tuya_local 12, smartthings 11). That is why the AC, Cameras and Quick
dashboards showed "Entity not found": their integrations no longer existed.

No Home Assistant backup existed to restore (`/backup` is not mounted, `/share`
is empty, `/BACKUP` has none).

Restored so far, via the config-flow API with the existing Hermes token:

- **Frigate** (`http://frigate:5000`) and **MQTT** (`mqtt:1883`, credentials
  from Frigate's environment). The deleted registry entries matched on
  `unique_id`, so every original entity ID came back - `camera.outdoor`,
  `binary_sensor.outdoor_*`, `sensor.outdoor_all_count`, `switch.outdoor_*` -
  and the Cameras dashboard works again.

Still missing, needs the owner:

- **SmartThings** (Samsung AC: `climate.samsung_room_ac` and the
  `samsung_airconditioner_*` sensors) - OAuth sign-in required.
- **Tuya Local** (12 entities) - device ID and local key per device.
- **localthings** (35 entities) - LG device keys.
- **mobile_app** (32 entities) - reopen the Companion app to re-register.

Prevention: mount a host directory for Home Assistant backups and enable an
automatic schedule; the current `backup` integration writes to `/backup`, which
is inside the container and is lost if the container is recreated.

## Local-only AC and bulb (2026-11-09)

The AC and the desk bulb are back **without any cloud integration**:

- **Samsung AC** - `localthings` (LocalThings, `iot_class: local_push`). The config
  flow only needed `host: 10.1.1.238`; it completed the certificate handshake
  itself, and the entry now holds the CA/leaf certificates and device key. All
  35 entities returned with their original IDs, including
  `climate.samsung_room_ac`. No SmartThings account or token was used.
- **Wipro bulb (behind monitor)** - `tuya_local` in manual mode with
  `device_id`, `host: 10.1.1.239` and the local key from the 1Password item
  "Wipro Bulb - Behind Monitor". `light.behind_monitor_bulb` is back.
- The **SmartThings cloud integration was deliberately not restored**; it
  controlled the same AC (`0f17ce84-...`) through Samsung's cloud and is
  redundant now that the local integration works.

Remaining lost entities are only `mobile_app` (32, re-register the Companion
app) and `upnp` (17, auto-discovered). No cloud dependency is needed for
lighting or cooling.

## Backups (2026-11-09)

Home Assistant writes backups to `/config/backups`, which is not configurable in
the Container install. It is redirected to the backup disk:

```text
/data/apps/homeassistant/backups -> /BACKUP/homeassistant   (host symlink)
stack mount: /BACKUP/homeassistant:/BACKUP/homeassistant
```

- Schedule: **daily at 03:00**, retention **7 copies / 30 days** (set through
  `backup/config/update`; stored in `.storage/backup`).
- Verified with two manual backups: the tars appear in
  `/BACKUP/homeassistant` and `/config/backups` resolves to the same files.
- `/BACKUP` is an fstab mount with `nofail`; if the USB disk is absent the
  symlink target falls back to the root filesystem. Check
  `mountpoint /BACKUP` if backups look misplaced.
