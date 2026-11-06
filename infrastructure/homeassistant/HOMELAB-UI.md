# Home Assistant dashboard UI

This is the surface-level UI contract for the native Homelab **Cameras** and
**Nodes** views and the Samsung AC **Care** view. It documents an ordinary
extension of Home Assistant, not a separate design system. The active Home
Assistant theme and frontend remain the source for color, typography, spacing,
card treatment, shape, elevation, icons, and responsive behavior. The dashboard
YAML adds no local visual tokens, custom theme, CSS, third-party card, frontend
dependency, or decorative image.

Owner reviewed the final live layout and confirmed **“looks good now”**. Preserve
this version; do not add explanatory cards or continue visual changes unasked.

## Surface rules

- **Cameras:** Keep the actual outdoor live video first, followed by the real
  motion, person, dog, and object states. Keep the existing detection,
  recording, and snapshot switches together under Camera controls, with the
  native Frigate navigation tile. The native Sections layout uses at most two
  columns on desktop and flows in reading order on a phone.
- **Nodes:** Keep px10, px20, and px30 as equally treated native groups. Each
  group shows its nine actual host readings and the six-hour CPU/RAM history
  graph. The Sections layout uses at most three columns and flows into one
  column on a phone. Metric definitions and limitations belong in
  [FRIGATE-AND-NODES.md](FRIGATE-AND-NODES.md).
- **AC Care:** Keep Device care, Filter & cleaning, and Local history as the
  native groups, with at most three desktop columns and one-column phone
  flow. Preserve current reported status and measurements. The
  self-check Markdown card is live status/result/error data, not explanatory
  copy, and should remain data-led. Care interactions and feature limits are
  documented in [SAMSUNG-AC-DASHBOARD.md](SAMSUNG-AC-DASHBOARD.md).
- Keep native labels concise and retain the data needed to operate the views.
  Put metric definitions, capability limits, and operational caveats in the
  linked runbooks instead of adding explanatory paragraphs to these views.

## Copy and safety boundary

The owner's latest preference is **no explanatory or helper-text cards** in
Homelab Cameras, Homelab Nodes, and AC Care. Do not add Markdown cards whose
purpose is to explain a capability or qualify a measurement on those surfaces.
This is a surface-specific copy rule; it does not create a global prohibition
for other Home Assistant dashboards.

This later preference supersedes the nearby-explanation guidance in the
AC-scoped [DESIGN.md](DESIGN.md) for these three surfaces only. It makes no
change to AC Control or unrelated interfaces. DESIGN.md remains as the AC
design record; this file records the later exception without rewriting it.

Keep all existing confirmation prompts for starting self-check, stopping a
running auto-clean cycle, and resetting the filter counter. The stop action is
visible only while cleaning is running. Both the card and icon taps must retain
the same confirmation-protected action. Keep the displayed self-check fields
as actual state, stored result, and reported error. Do not add unsupported
controls, imply cloud-only features are local, or turn live measurements into
a fabricated health score.

## Evidence and finish review

Implementation sources are [dashboard-homelab.yaml](dashboard-homelab.yaml)
and [dashboard-samsung-ac.yaml](dashboard-samsung-ac.yaml). Context sources
are [PRODUCT.md](../../PRODUCT.md) (AC-scoped), [homelab-direction.md](homelab-direction.md),
[DESIGN.md](DESIGN.md), and [FRIGATE-AND-NODES.md](FRIGATE-AND-NODES.md).

All six final desktop and phone captures were independently opened and reviewed
at 1440 px and 390 px. The fresh visual disposition is **ship**:

- [Cameras desktop](../../.impeccable/review/homelab/cameras-desktop.png) and
  [Cameras phone](../../.impeccable/review/homelab/cameras-mobile.png) show the
  live camera before its state tiles and controls, with no explanatory card.
- [Nodes desktop](../../.impeccable/review/homelab/nodes-desktop.png) and
  [Nodes phone](../../.impeccable/review/homelab/nodes-mobile.png) show all
  three host groups and their history graphs in the expected responsive order.
- [AC Care desktop](../../.impeccable/review/samsung-ac/care-desktop.png) and
  [AC Care phone](../../.impeccable/review/samsung-ac/care-mobile.png) show the
  three Care groups, actual self-check data, maintenance values, and history
  without explanatory cards.

The captures have no visible horizontal overflow or native error cards. The
Homelab review record reports live H.264 video at 1920×1080 (player ready state
4, unpaused, with advancing time) at both widths and 27 numeric node sensors
verified. The AC review record confirms that the three maintenance actions
remain confirmation-protected on both card and icon taps. These records are
runtime evidence; this document pass reviewed the source, review records, and
captures and did not repeat browser or device actions. Captures show the light
theme; dark appearance continues to be owned by Home Assistant.

## Nodes redesign, 8 November 2026

Proxmox is retired, so Nodes describes the single `l3b` host. Native Sections
cards only, no custom card, CSS, theme or helper text. Verified by screenshot at
1920, 1100 and 390 px wide. Heading badges were dropped because they were hard
to find; every value is now a readable tile.

`max_columns: 4`, three sections each with `column_span: 4` (48 grid columns on
desktop, 12 on a phone), so `grid_options.columns: 6` gives eight across on
desktop and two across on a phone:

- **l3b:** eight `tile` cards with the native `bar-gauge` feature: CPU, Memory,
  Swap, Temperature, Root, Data, Backup, Load (bar maximum 6, the CPU count).
- **Docker and system:** eight plain tiles: Running, Total containers, Stopped,
  Unhealthy, Failed services, Images, Network down, Uptime.
- **Last 6 hours:** four `history-graph` cards (`columns: 12`): CPU and memory,
  temperature, load, network down and up.

Values are `sensor.host_*` REST sensors polling `homelab-stats`, which now also
reports container totals, stopped, image count, failed systemd units and `eno1`
throughput (5 s background sampler). No synthetic health score. Tile bar colours
are static. The graphs only reach back as far as the sensors have recorded.
Tracked copies: `config/homelab.yaml`, `config/homelab_metrics.yaml`.

### Threshold colours, 8 November 2026

Tile bar colours now follow the value using native card `visibility`
`numeric_state` conditions: one tile variant per state (green, orange, red, and
grey while the sensor is unavailable), and Home Assistant renders exactly one.
No custom card or CSS. Thresholds (warn / critical):

| Tile | Orange above | Red above |
|---|---|---|
| CPU | 70 % | 90 % |
| Memory | 80 % | 92 % |
| Swap | 60 % | 85 % |
| Temperature | 75 C | 90 C |
| Root | 75 % | 90 % |
| Data, Backup | 80 % | 92 % |
| Load (1 min, 6 cores) | 6 | 9 |

Unhealthy and Failed services are green at zero and red above. Stopped stays
grey: `sandbox-certs` is a one-shot job that exits 0, so 1 is the normal value.
Network up now has its own tile; Images was dropped.

The Nodes view is generated, not hand-edited:
`python3 infrastructure/homeassistant/generate-nodes.py /data/apps/homeassistant/dashboards/homelab.yaml`
keeps the Cameras view and rewrites Nodes. Long-term `statistics-graph` cards
were tried and left out: the new sensors have no compiled statistics yet, so they
showed "No statistics found". Add them once a week of data exists.

## Overview as the quick-use page, 8 November 2026

The owner wanted the **Overview** itself to be the quick-use page, not a separate
dashboard, so the earlier extra "Quick" dashboard was removed.

In this Home Assistant version the system default dashboard is the generated Home
page (`/home/overview`, system data `default_panel` = `home`). The classic
Overview (panel `lovelace`) is storage mode, so it was taken over and its config
saved through the `lovelace/config/save` WebSocket call from `config/overview.yaml`
(converted to JSON), and `default_panel` was set to `lovelace` with
`frontend/set_system_data` (key `core`, other keys preserved). The Overview now
opens at `/lovelace/default_view` and is first in the sidebar.

The layout is generated: `python3 infrastructure/homeassistant/generate-overview.py /tmp/overview.json`,
then send it with the `lovelace/config/save` WebSocket call. Native Sections
cards only, verified at 1920 and 390 px. Controls first, status last:

- **Room:** bulb tile with brightness slider; Room AC tile with the five HVAC
  modes and target temperature.
- **Outdoor:** snapshot picture (`camera_view: auto`; tap for the live stream;
  `live` rendered blank in headless Chromium).
- **Switches:** two-across tiles for Detection, Recording, Snapshots, Camera
  alerts, AC schedule and AC alerts.
- **Homelab (`column_span: 3`):** the same threshold-coloured bar tiles as Nodes
  (CPU, Memory, Temperature, Root, Data, Backup) plus Containers running and
  Unhealthy containers, all tapping through to the Nodes view.

The first version had three columns of uneven height, a flat blue status block
and one tall switch list; this one matches the Nodes view and is shorter on a
phone. Only `climate.samsung_room_ac` is shown; `climate.bedroom_1_ac` is a
duplicate cloud entity.

To revert to the generated Home page: send `lovelace/config/delete` and set
`default_panel` back to `home`.

The Samsung AC dashboard is now titled **AC** in the sidebar and in
`dashboard-samsung-ac.yaml`. Its URL stays `/samsung-ac/...` so existing links
keep working. A dashboard title change in a package needs a Home Assistant restart.
