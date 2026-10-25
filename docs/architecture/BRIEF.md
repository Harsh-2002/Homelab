# Architecture diagram brief

## Superseding owner direction, 2026-10-25

The owner rejected the presentation/inventory-sheet design below. This task is
for his internal understanding, not primarily public sharing. Build a connected
tree with IP/ports: router, LAN switching/AP, camera/bulb/AC, physical Proxmox
hosts, VM/LXC guests, Docker stacks/individual containers, Kubernetes logical
services and storage. On the same native editable Excalidraw scene, trace the
important request/data paths in focused frames. Use the explicitly chosen
official Excalidraw CLI. Unknown device/cable details remain marked unknown.
No API key, Excalidraw+ login, remote uploads or new hosted service required.

The direction contract is now a tree/map with short node labels and arrows, not
paragraph cards. Existing cool neutral technical palette is retained only for
legibility. Earlier review approval does not override the owner's rejection.
Native scene, text, bound arrows and frames must be independently rendered and
reviewed. Root Home Assistant product context remains outside scope.

Scope: docs/architecture only. Read mode. Anurag wants a complete, minimal,
professional explanation of physical compute and services, using his supplied
network diagram as subject reference, not as infrastructure evidence. Readers
include engineers outside the homelab. Public and internal-IP editions required.
Preserve the existing AC product/design context outside this directory.

## Direction contract

THESIS: Show actual host containment first and important end-to-end relationships
second. Two coordinated sheets replace one illegible map of every packet.

OWN-WORLD: Owner-pinned clean technical schematic. Cool near-white paper,
dark blue-grey text, fine orthogonal lines, restrained blue cluster grouping and
teal data/dependency accents. Plain sans-serif labels; geometry, not clip-art.

STORY: Access paths lead into three real Proxmox hosts; Talos VMs converge on
one cluster. The second sheet traces identity, GitOps, memory, media and home
automation. Private IP edition adds a third endpoint sheet, never public Git.

FIRST VIEWPORT: 2400 × 1820 landscape sheets, full-width access band above three
equal physical-host columns, shared cluster below and compact boundary notes.
No motion or controls; zoomable SVG and PDF preserve readability in print.

FORM: User-pinned engineering schematic / architecture-as-code. Seed 5574fecf
was run; the explicit minimal technical reference takes precedence over random
visual identities. Code-led geometry, no generated imagery or external assets.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
