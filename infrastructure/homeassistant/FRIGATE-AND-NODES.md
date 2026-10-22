# Frigate and physical-node monitoring in Home Assistant

Deployed 2026-10-22, Core2026.10.2. Owner requested existing Frigate integration
and basic px10/px20/px30 host stats, then explicitly requested no descriptive
paragraphs on Nodes/Cameras/AC Care. Native cards only; AC Control unchanged.

- [Cameras](https://home.l3b.cc.cd/homelab-status/cameras)
- [Nodes](https://home.l3b.cc.cd/homelab-status/nodes)
- [Samsung AC Care](https://home.l3b.cc.cd/samsung-ac/care)

## Architecture and authentication

Frigate0.18.0 remains Portainer stack137 on endpoint2/ctr10.1.1.4. Official
Frigate HA integration **v5.15.6** installed manually under
`/config/custom_components/frigate`; no HACS dependency added. Upstream tag
archive SHA256 `a759a2fa7c773e90f8560f1d212c9a30ca26e786309a03350ae5b468b2ecd7aa`.
All32 selected archive members checked against path traversal and symlinks.
Entry `01M5HW0D3QK3J8SGZ7HZYQQ7VS`, URL `https://frigate.l3b.cc.cd`, TLS
verification enabled. Do not point at the Docker registry on ctr port5000.

Existing Frigate MQTT target10.1.1.40:1883 was unreachable. HA had no MQTT entry
or broker. Installed official Mosquitto app7.1.2 on HAOS, auto-start/watchdog,
only port1883 published; unused WebSocket/TLS listeners not published. Anonymous
MQTT rejected. Reused existing Frigate MQTT login/password, already in
HomeLab/Frigate (MQTT Password). HA and Frigate have distinct client IDs on the
same broker10.1.1.13; Frigate's Portainer environment now points there. MQTT
traffic is authenticated plaintext on private LAN, not a public service. Native
MQTT flow uses protocol3.1.1 and the current nested `other_settings` schema.

Caddy adds a source-IP-specific handler only for the HA VM10.1.1.13 on the
existing private Frigate hostname. It supplies the existing proxy secret and
machine identity `homeassistant` with the mapped admin group; normal browser
requests still go through Pocket ID/Tinyauth. Source restriction uses actual
`remote_ip`, not spoofable X-Forwarded-For. Verified HA API200, non-HA401 even
with forged X-Forwarded-For. The machine path grants Frigate controls to HA;
it is not a new public auth-free endpoint. Keep the HA IP reserved/static.

Restream is bound only to10.1.1.4:8554, with separate username/password saved
concealed as RTSP Username/RTSP Password in the existing HomeLab/Frigate item.
Anonymous RTSP DESCRIBE401; authenticated DESCRIBE200. HA stores the credential
in its protected integration options, not dashboard YAML. Frigate's unauthenticated
port5000 remains unpublished;8555/WebRTC not additionally exposed. Notification
proxy endpoints disabled because notification access was not requested; media
browser enabled. Frigate-native WebRTC option off, HA's normal player used.

## Browser video compatibility

The source `outdoor` stream is **H.265**. Initial browser playback failed despite
working snapshots and live MQTT entities. Added `outdoor_ha` as an on-demand
go2rtc restream:

```yaml
go2rtc:
  streams:
    outdoor_ha:
      - "ffmpeg:outdoor#video=h264#hardware=vaapi#raw=-vaapi_device /dev/dri/renderD128"
```

VAAPI conversion initially failed with `A hardware device reference is required
to upload frames to`. Explicit `-vaapi_device /dev/dri/renderD128` resolved the
upload context. Existing Intel device passthrough and i965 driver reused.
No additional GPU/agent/container introduced. Transcoding runs on demand when
this HA stream is consumed, not by changing the recording/detection pipeline.
Native Frigate recordings remain the original H.265 copy with seven-day
motion/event retention. No recordings/database deleted.

HA RTSP URL template is authenticated `rtsp://<user>:<secret>@10.1.1.4:8554/{{ name }}_ha`.
Future cameras require matching `<name>_ha` restreams, or revise the template;
never point every camera at outdoor. Localhost Frigate RTSP inputs retain the
documented loopback authentication exemption. Frigate config changes deployed
through Portainer stack update and targeted container restart, not an unmanaged
parallel Compose stack. Short startup recording gaps occurred; existing data
and retention were preserved. No claim of zero recording downtime.

## Physical node sensors

Reuse Node Exporter → VictoriaMetrics; no new host agent, SSH polling or PVE
administrator token in HA. `/config/packages/homelab_metrics.yaml` makes one
authenticated MetricsQL query per60seconds and extracts27 sensor values.
Existing VictoriaMetrics password is copied only into protected
`/config/secrets.yaml` as `ha_victoriametrics_password`; source contains `!secret`.
Credential remains in HomeLab/VictoriaMetrics API as before. API stays LAN-only.

Each of px10/px20/px30 has nine sensors:

| Reading | Meaning |
|---|---|
| CPU |100 minus mean per-core idle rate over2minutes. |
| RAM percent/used/total |MemTotal minus MemAvailable, not summed VM reservations. GiB binary units. Includes Linux/ZFS host memory accounting. |
| ZFS pool used/free |Sum of local ZFS pool allocation/capacity, free inGiB. Not shared SMB storage or guest filesystem occupancy. Existing textfile collector updates every5minutes. |
| CPU temperature |Maximum coretemp package/core reading, Celsius. Not ambient temperature. |
| NVMe temperature |Maximum composite `temp1` reading across NVMe devices, not arbitrary hottest NVMe sensor. |
| Uptime |Hours since host boot; native HA formats duration. |

Queries filter physical `host` labels and gate measurements on current exporter
`up==1`. Missing results become unknown rather than fabricated zeros. The
backend itself has normal time-series lookback/staleness semantics; this is
polling, not instantaneous failure detection. History begins when HA records
the new entities. No Talos VM stats mislabeled as px hosts. Detailed history
and storage breakdowns remain in existing Grafana.

px10 exporter was failed after boot: `listen tcp10.1.1.10:9100: bind: cannot
assign requested address`, followed by restart-limit exhaustion. Added tracked
`infrastructure/metrics/node-exporter-network.conf` to all three nodes at
`/etc/systemd/system/prometheus-node-exporter.service.d/network.conf`: wants/
after network-online,15second retry and no start-limit interval. Listener remains
strictly each node's LAN IP. All three restarted and verified active/enabled;
no host reboot performed. Actual reboot recovery remains untested. px30's
separate thermal_zone collector has unsupported-data warnings; hwmon temperatures
work and are used here. No unrelated collector changes.

## UI and safety

Native Homelab/Cameras has live16:9 video, compact motion/person/dog/object tiles,
explicit existing recording/detection switches and a Frigate navigation tile.
Homelab/Nodes has three consistent node panels and six-hour CPU/RAM graphs.
No descriptive Markdown cards, as explicitly requested. Definitions stay here.

AC Care keeps actual status, counters, filter interval and history. Explanatory
and unsupported-feature paragraphs removed; no unsupported controls added.
Large maintenance buttons replaced with full-width native tiles. Both card-tap
and icon-tap are bound to the **same confirmation-protected action**. Stop-clean
still appears only during cleaning. Actual self-check state Markdown remains
because it is data, not explanatory prose. No maintenance action executed.

## Reproduce, verify, rollback

Native pre-change HA backup **80f021c0**,11,141,120bytes, includes HA config/DB.
Frigate original config retained as
`/data/apps/frigate/config/config.before-ha-20261022.yml`; Caddy original at
`/etc/caddy/Caddyfile.before-ha-frigate-20261022`. Secrets-file original retained
before its single protected addition. Two checked Core restarts loaded the
component and new YAML integration; dashboard-only edits need no restart.

Tracked artifacts map to:

- `dashboard-homelab.yaml` → `/config/dashboards/homelab.yaml`.
- `packages/homelab_metrics.yaml` → `/config/packages/homelab_metrics.yaml`.
- Existing package include is reused; don't replace `configuration.yaml`.
- Frigate compose/config placeholders live under `infrastructure/frigate/`.
- Caddy source is `infrastructure/proxy/Caddyfile`.
- `frigate-setup.py` has explicit operator phases. It reads existing protected
  HA/operator credentials into memory; never print expanded environments,
  config entries or RTSP URLs. Inspect before execution. The stack helper
  preserves unrelated live stack fields; runtime config helper merges only
  RTSP auth and the outdoor_ha restream. One-time mqtt/metrics-secret phases
  refuse replacing preexisting data. Requires PyYAML and operator SSH/op access.

Read-only verification (temporary venv needs websockets):

```bash
/tmp/samsung-ac-investigation-venv/bin/python infrastructure/homeassistant/verify-homelab.py
python3 infrastructure/agents/check-integrations.py
```

Verified27 live numeric sensors, all three exporters, camera still200/JPEG,
media browser3top-level entries, authenticated HLS master/media playlist and
14MB video segment. Verification decompresses gzip; raw compressed playlist
bytes must not be mistaken for invalid HLS. Browser video1920×1080, ready4,
unpaused with advancing currentTime, at desktop1440 and phone390. All six final
Cameras/Nodes/AC Care captures opened valid, no overflow/error cards. Existing
bulb/AC entities available. MQTT source10.1.1.4 connected as frigate and native
motion state changed naturally. No detector/recording/appliance control commands
sent, no fabricated detection test. Real hardware reboot/outage not exercised.
No agent MCP/config changes; four-agent parity checker passes.

To roll back, remove only Frigate/MQTT entries and newly installed component/
Mosquitto app if no later consumers depend on them. Restore saved Frigate/Caddy
config and prior stack environment/port mappings, then validate/reload. Do not
restore the old unreachable MQTT broker merely to recover healthy recording.
Remove new HA Homelab package/dashboard and secret only if no later references;
check Core config before restart. Exporter retry drop-in is independently
reversible; don't remove healthy existing exporters or their historic metrics.
Never delete recordings, databases, existing HA auth, bulb or AC integrations.

Sources: [Frigate HA integration](https://docs.frigate.video/integrations/home-assistant/),
[RTSP/restream authentication](https://docs.frigate.video/configuration/restream/),
[integration v5.15.6](https://github.com/blakeblackshear/frigate-hass-integration/releases/tag/v5.15.6),
[HA REST integration](https://www.home-assistant.io/integrations/rest/).
