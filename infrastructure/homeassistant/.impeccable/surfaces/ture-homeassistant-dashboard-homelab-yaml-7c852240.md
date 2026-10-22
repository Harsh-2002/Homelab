---
version: 1
slug: "ture-homeassistant-dashboard-homelab-yaml-7c852240"
primary_target: "dashboard-homelab.yaml"
related_targets: []
---

# Homelab dashboard

Target: infrastructure/homeassistant/dashboard-homelab.yaml
Mode: Operate. Ordinary native Home Assistant extension, not a new visual world.

THESIS: Add usable Frigate camera access and basic physical Proxmox node stats.
OWN-WORLD: Inherit native HA cards, theme, typography and responsive Sections.
STORY: Cameras shows live outdoor video, real detection state and existing
recording controls; Nodes shows px10/px20/px30, never Talos VM statistics.
FIRST VIEWPORT: Real camera first in Cameras; equal, clearly named node panels
in Nodes. One-column phone flow, no descriptive/helper cards, no invented health score.
FORM: Native cards, no imagery/mockup round or custom frontend. Preserve existing
bulb/AC dashboards. Two views separate security-camera use from infrastructure.
FINISH: Desktop/phone capture review, entity and actual video verification,
reproducible deployment docs and honest metric definitions. Inherit existing
DESIGN.md without new token system. No shipping raster assets.
