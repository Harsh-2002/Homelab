# Architecture diagram brief

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
