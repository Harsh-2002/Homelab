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
