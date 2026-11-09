# Smart Plugs dashboard

Primary target: dashboard-smart-plugs.yaml. Mode: Operate.
Owner requested a dedicated sidebar dashboard like the AC dashboard, ready for
the current gaming-PC 10A plug and two later plugs (another 10A and one 16A).
Visible device name is **PC**; keep ratings out of titles and the dropdown.

## Direction contract

THESIS: Monitor real plug measurements first, with deliberate controls separated
from observation. Do not create placeholder entities or pretend other plugs are
already paired.

OWN-WORLD: Native Home Assistant theme, Sections layout, tiles, history graphs,
entities and confirmation-protected buttons. No custom frontend dependencies.

STORY: One common dashboard and one plug dropdown choose whose measurements,
history and settings are visible. No per-plug dashboards or separate views.
Power/protection/lock actions require confirmation. No device commands run as
part of deployment or QA.

FIRST VIEWPORT: Plug filter first, then socket state and live readings, clearly
labelled calculated energy and local history. Settings below. Three columns
desktop, single flowing column on phones.

FORM: Extend the existing native HA visual world. Add selector options and
conditionally visible sections when other devices are actually authenticated;
only the selected device's sections render. Keep limits and energy sources
separate; never target an entire device group from the filter.

FINISH: Desktop/phone review, no missing entities, cancelled power confirmation,
live read verification and reproducible deployment documentation. No shipped
raster assets; inherit DESIGN.md's native interface language.
