# Wipro / Smart Life bulb: local-control investigation

Status on 2026-10-22: **local Home Assistant control is configured and tested.**
The owner approved Smart Life authorization, the account device matches the
discovered endpoint, and native local light commands/read-back pass. A physical
WAN-outage/long-duration cloud-block test is still unperformed; do not claim that
acceptance test passed or that the stock firmware never contacts its cloud.

## Current operational access

- Device: **Behind Monitor Bulb** (Smart Life product label Smart Light).
- Entity: **light.behind_monitor_bulb**.
- Integration: Tuya Local2026.9.2, loaded, protocol3.3, host10.1.1.231.
- Config entry: `01M5HMSTDVDVH2BWSADBZWER1J`.
- Profile: **rgbcw_lightbulb**, whose declared product identifier matches the
  observed broadcast product ID and whose datapoint types match the real bulb.
  Do not use the first suggested xld_cl002 profile or an inverted-temperature
  profile merely because a generic match ranks higher.
- Secret: **HomeLab → Wipro Bulb - Behind Monitor**, API Credential item.
  The local key was saved concealed and verified against the authorized setup.
  Native HA config stores device_id,host,local_key,poll_only,protocol_version,type,
  not the cloud authorization token. Never dump those config values.
- Normal access: existing private **https://home.l3b.cc.cd**, native HA mobile
  app/dashboard and authenticated REST/WebSocket APIs. Hermes's existing Home
  Assistant plugin can operate this entity; other authorized agents can reuse
  the same existing HA API access. No extra agent MCP, public webhook or broker.

Verified native API requests use the existing HA bearer credential, obtained
privately from its canonical vault item or protected runtime, never source code:

```text
GET /api/states/light.behind_monitor_bulb
POST /api/services/light/turn_on
{"entity_id":"light.behind_monitor_bulb","brightness_pct":20}

POST /api/services/light/turn_on
{"entity_id":"light.behind_monitor_bulb","hs_color":[210,70]}

POST /api/services/light/turn_on
{"entity_id":"light.behind_monitor_bulb","color_temp_kelvin":4000}

POST /api/services/light/turn_off
{"entity_id":"light.behind_monitor_bulb"}
```

Local authenticated status reported datapoints20(power),21(mode),22(brightness),
23(white temperature),24(HSV),25(scene data),26(timer),34(do-not-disturb). Tested
HA brightness34/255, HS210/70, white4500K(request)/4501.2K(read-back), off and
on. Finally restored **on/color_temp/brightness24/3376.4K**, matching original HA
visible state. Conversion can round native brightness; this is not a claim that
every cached raw datapoint byte was restored. Timer and do-not-disturb entities
are exposed but not changed. Scene effects were not exhaustively tested.

Authenticated state read through private HTTPS passed. Native integration reload
returned require_restart:false and reconnected to on/white brightness24. Normal
operation uses the local key, not periodic Smart Life account authentication.
Do not reset/re-pair casually because the local key can change.

## Target and observed evidence

The owner supplied Wi-Fi interface label wlan0, MAC10:5A:17:51:D7:9D and
candidate10.1.1.231, with the bulb currently lit and controlled by an app.
The owner subsequently confirmed the current app is **Smart Life**, formerly
Wipro Smart. The interface label is from the router, not a devVM interface.

- Three bounded ICMP probes succeeded. Linux neighbor discovery independently
  mapped10.1.1.231 to10:5a:17:51:d7:9d on dev eth0.
- IEEE OUI registration105A17 is Tuya Smart Inc. This identifies the module
  manufacturer, not an exact Wipro model or firmware/chip revision.
- A small TCP connect check found6668 open. Ports80,443,1883,8080,554 gave no
  response within1.5s. This is a bounded observation, not proof of no other ports.
- TinyTuya1.20.0 discovery, without polling or force-scanning, found the target
  advertising version3.3, encrypt:true, a device ID and product identifier.
  No local encryption key is present in these announcements.
- Seven target-originated UDP broadcast frames were captured over30seconds.
  All seven decrypted as discovery announcements using TinyTuya's public
  discovery decoder and referred to the same device ID.
- REA6.7.0 inspected the actual capture using Wireshark/TShark4.4.19 and capinfos.
  The packet-field view independently showed the supplied MAC on all seven
  source-IP-filtered frames. No firmware, app APK or unknown binary was supplied
  or decompiled. This is packet/protocol investigation, not broken encryption.

REA summary Evidence ID:
`ev_8a87ac47ca3f393759157c0fe5a00ea4683c62861a63d79482189dcae70f0ba8`.
Packet-field Evidence ID:
`ev_cfe6ad9556d6a22f40ed00dfb54849b04b93f0500d62f4b2aca1be3e7e18ee05`.
Capture SHA256:
`07e3f97a024ec6c5742c6e5a6022dbec64f75f1599575d32b3b3154a3e1d6350`.

Private capture on dev:
`~/.local/state/bulb-investigation/tuya-20261022.pcap` (0600,parent0700),1634bytes.
It contains only traffic visible to the dev VM under the exact target filter;
this switched LAN capture does not see all phone-to-bulb or bulb-to-WAN traffic.
No DNS/SNI observations in this capture do not prove the bulb avoids the cloud.
Do not commit raw captures, device keys or account authorization data.

The owner-authorized account contained Behind Monitor Bulb, whose device ID
exactly matched the broadcast device. This confirms the account-device mapping;
the physical model/chip revision remains unknown.10.1.1.231 was historically a
temporary HAOS address; HAOS is now10.1.1.13. Live MAC evidence overrides history.

During actual control, a second private capture on px30 vmbr0 recorded39frames
between HA10.1.1.13 and bulb10.1.1.231, with23payload-bearing TCP frames on the
HA ephemeral port↔bulb6668 connection. REA Evidence:
`ev_a1005f573748cd545f39bd8e08beb3d499d942b9cc68f4c0d1e2d2952c1ba43e`.
Capture: `~/.local/state/bulb-investigation/ha-local-control-20261022.pcap`,0600,
5220bytes,SHA256
`41f8212b18d890784b48ec83e545a2cc90c43563b3c4f238d270342dd05b4172`.
The capture filter selected that LAN conversation; it proves the observed local
path, not absence of unrelated WAN traffic. Wireshark heuristically labeled
three encrypted TCP frames ipdc; that does not identify this bulb as a VoIP device.

## Chosen implementation

Use maintained third-party **make-all/tuya-local**, not Home Assistant's built-in
Tuya cloud integration. Its cloud-assisted setup can retrieve the local key
through owner-approved Smart Life account linking without an IoT developer
account. That is a one-time setup dependency; normal device control is local.
The stock bulb firmware may continue contacting its vendor cloud until separately
restricted. Long-duration WAN-off behavior remains untested and must not be
promised from protocol discovery alone.

Reuse Home Assistant as the authenticated local API and automation controller,
rather than deploy a redundant bridge/broker/API service. Hermes already has
the Home Assistant integration. Other authorized agents/apps can call Home
Assistant's existing REST/WebSocket API after the light entity is configured.
No new public endpoint or anonymous webhook is required.

## Preparation actually completed

- HA Core2026.9.4 at10.1.1.13 verified by authenticated native API.
- No existing tuya,tuya_local,localtuya or HACS config entry/component was found.
- Native pre-change backup **a8059954**, name before-tuya-local-20261022,
  completed successfully; reported size6.27MB. Keep it private on HAOS.
- Installed official tagged **Tuya Local2026.9.2**, release2026.9.2-rel,
  under `/config/custom_components/tuya_local` through the existing SSH app.
  No HACS installation or Home Assistant version upgrade was needed.
- Release hacs.json minimumHA2026.8.0 is compatible with installed2026.9.4.
  Manifest pins tinytuya1.20.0 and tuya-device-sharing-sdk~=0.2.4.
- Downloaded archive SHA256:
  `90c76dae12e2f59548920808c5f08d6ced51af2fb186aee0de5d2a8ba480ebf6`.
  Selected component members checked for symlinks and traversal before extraction.
- `ha core check` passed. One controlled **Core restart**, not VM reboot,
  completed; authenticated API returned2026.9.4 afterward.
- Native tuya_local flow opened successfully. After owner-supplied User Code and
  Smart Life QR approval, the agent completed account-device selection, local
  discovery, authenticated connection, exact product/profile matching and naming.
  Authorization codes/QR tokens are not retained in documentation or memory.

TShark/capinfos4.4.19 were installed on dev for REA packet analysis (11packages,
approximately141MB). Existing non-root capture privilege settings were not
expanded. TinyTuya1.20.0 is in a temporary diagnostic venv at
`/tmp/wipro-bulb-investigation-venv`; recreate it if /tmp is cleared. No diagnostic
daemon, permanent scanner, new MCP server or agent permission change was added.
The four-agent MCP parity check still passes.

## Reauthorization procedure (only if needed later)

In private Home Assistant:

1. Settings → Devices & services → Add integration → **Tuya Local**.
2. Choose SmartLife cloud-assisted setup.
3. In Smart Life: Me → Settings → Account and Security → User Code. Enter that
   case-sensitive code directly in Home Assistant where practical, not Git.
4. Scan Home Assistant's QR in Smart Life and approve the account link. Continue
   in Home Assistant until the account-device list appears. Agents may complete
   the flow for the owner; QR approval still requires the owner's phone.
5. Close Smart Life after approval before testing the local connection; some
   Tuya devices permit only one LAN client at a time.

If the new integration does not appear, refresh the browser after the Core
restart. User approval cannot be substituted by a fabricated key or bypassed QR.
Do not reset/re-pair the bulb: that can rotate the key and change its IP.

## Remaining acceptance checks

- Account mapping/key retrieval, local status, profile selection, entity creation,
  power/brightness/color/white-temperature and integration reconnect checks passed.
- Verify a complete cold restart and controlled bulb-only WAN-disconnection behavior,
  including an extended interval if the stock firmware stalls without cloud.
  No router/global internet changes were made during discovery.
- Consider a router DHCP reservation after identity is certain; no static lease
  or router configuration has been changed yet.
- Private HTTPS API state access passed. Hermes uses that same HA API via its
  existing plugin; a real conversational Hermes-triggered action remains untested.
  No new per-agent bulb integration is needed when using shared HA.

No firmware flashing, reset, Wi-Fi change, WAN block, or router ACL mutation was
performed. Only bounded announced light-control tests were performed and the
original visible on/white settings were restored afterward.

## Reproduction and rollback

For read-only identification, use `ip neigh show 10.1.1.231`, a bounded target
probe and TinyTuya deviceScan with poll=False/forcescan=False. Use selected
TShark fields or REA inspect-pcap-capture against the private capture above.
Do not rerun broad scans or print payload/account keys into transcript capture.

To reinstall the integration, obtain the same official2026.9.2-rel archive,
verify its hash, copy only custom_components/tuya_local to the equivalent HA
directory, check configuration and restart Core. Preserve other components.
For rollback, remove only a verified newly created tuya_local config entry
through the UI, remove only that custom-component directory if authorized,
and restart Core. Use native backup a8059954 only if broader recovery is needed;
do not overwrite newer HA changes casually.

Sources: [TinyTuya](https://github.com/jasonacox/tinytuya),
[Tuya Local release](https://github.com/make-all/tuya-local/releases/tag/2026.9.2-rel),
[Tuya Local account flow](https://github.com/make-all/tuya-local/blob/2026.9.2-rel/custom_components/tuya_local/config_flow.py),
[Home Assistant cloud Tuya](https://www.home-assistant.io/integrations/tuya/),
[IEEE OUI registry](https://standards-oui.ieee.org/oui/oui.txt).

## Public article

Published with explicit owner approval on 2026-10-22:
https://firstfinger.io/wipro-bulb-local-control-home-assistant/ . Firstfinger
commit `9a0143b59da625a77c4d70cf95f98c16694fc294`, pushed to main, `draft: false`.
Cloudflare Pages deployment succeeded and live HTTP 200 confirms the article,
both SVGs and owner-selected thumbnail `photo-1773301885514-a1ef2fd93f43`.
This supersedes the draft-only review history below. GitHub Actions lint/build
jobs failed separately during npm tooling installation before validation;
Cloudflare production deployment is successful. No CI configuration changed.

Owner requested a natural, concise first-person article matching the latest
Firstfinger posts, including inline SVG diagrams and an Unsplash cover.
Blog repository: https://github.com/Harsh-2002/firstfinger, local clone
`/home/dev/firstfinger`. The repository currently configures **firstfinger.io**;
the owner mentioned firstfinger.in, so do not silently change the site's domain.

Draft: `content/posts/wipro-bulb-local-control-home-assistant/index.md`, title
**Why Does My Light Bulb Need the Internet?**, `draft: true`. It records the
actual protocol investigation and existing open-source tools, not firmware
decompilation, broken encryption or a newly discovered exploit. Omits LAN
addresses, MAC/device IDs, keys, authorization codes and raw packet captures.
Two responsive accessible inline SVGs explain bootstrap versus runtime control
and the shared Home Assistant API. External Unsplash illustration is credited
and explicitly not a photograph of the actual Wipro bulb. Normal LAN control
is verified; extended WAN-outage/cold-start acceptance remains unperformed.
Draft is not published. Recheck HA compatibility and acceptance after the
owner's in-progress Home Assistant update before changing operational claims.

Draft validation: checksum-verified Hugo 0.161.1 builds with drafts enabled;
ordinary production build excludes the new post. Markdown lint and both SVG
XML/accessibility-title checks pass, and the rendered page was inspected in a
browser. Full-page HTML validation reports the existing shared template's
`ariaLabel` heading-anchor casing errors, not new article/SVG errors; the
unchanged template is outside this article's scope. Preview screenshot is
private under Homelab `.playwright-mcp/firstfinger-bulb-article-preview.png`.
