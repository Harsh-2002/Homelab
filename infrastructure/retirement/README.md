# Data backup for migration away from Proxmox

The owner plans to sell px10, px20 and px30 and later run a single Linux host.
The requested deliverable is actual application files, configuration and logical
database exports, **not VM images or retained VM/container snapshots**.
The original internal disks must remain intact until backup verification and
owner acceptance. Selling hardware is not authorization to erase those disks
before a separate reviewed handover.

## Destination and sequencing

The external Crucial X9 Pro 4TB drive was verified by its existing physical
identity before formatting. It now has one GPT Linux partition, ext4 label
`HOMELAB_BACKUP`, mounted temporarily at `/mnt/homelab-retirement`. No LVM,
Proxmox or ZFS tools are needed to mount the completed backup on another Linux
host. No automatic mount dependency was added to the retiring hosts.

The old AV/BACKUP LVM layout and old native VM-image archives were removed with
owner authorization. Approximately75GiB of media was first copied to internal
staging and compared successfully, then copied back to the new filesystem.
The separate256GB USB ISO disk was not formatted. Existing media and ISO SMB
services are currently unavailable: Store109 is stopped, the old CIFS storage
entries and old AV/BACKUP mount units were disabled deliberately.

Finish and verify **all px10/dev work first**. Flush and normally unmount the
external drive; only then ask the owner to move it to px20. Verify the same
physical disk, filesystem UUID from its `BACKUP-DISK.json`, and marker after
reattachment. Finish CTR and remaining px20 guest data locally over the host's
virtual network, not by relaying bulk bytes through dev over physical LAN.

## File layout and consistency

`homelab-backup-2026-10-31/` contains:

- `dev/rootfs/`: files from the live dev VM, including user homes, all working
  copies/uncommitted files, hidden agent state, SSH keys, configuration and tools.
  Virtual filesystems, temporary mounts, external shares and swap are excluded.
- `dev/consistent-sqlite/`: online SQLite backups of seven OpenCode/Hermes
  databases, checked with `PRAGMA quick_check`; `restore-map.json` records paths.
- `containers/`: cold file copies and PVE config references. Unprivileged LXC
  ownership is translated back to normal guest UID/GID, not retained as100000+.
- `hosts/`: host configuration, private cluster files, installed-package lists,
  storage/placement inventory, scripts and journals. No internal disk images.
- `kubernetes/`: all113 listable non-event resource types, including secrets,
  CRDs, RBAC, GitOps objects and PVC definitions; direct Talos machine configs;
  etcd state database; complete PostgreSQL SQL export; functions/snippets and
  storage-object file archives. The etcd export is logical cluster recovery
  state, not a virtual-machine image.
- `ctr/`: planned ordinary Linux application files, bind data, named Docker
  volumes, Compose/Portainer definitions, private container metadata and logical
  database exports. Exclude re-downloadable Docker/containerd image caches;
  retain registry blobs because those are application data.
- `orva/`, `home-assistant/`: portable service configuration and data.
- `media/`: media files retained from the original AV volume.
- `manifests/`: per-component completion, checksums and limitations.

Do not mark a planned directory complete just because it exists. The current
ledger/status files on the external drive determine actual completion.
Services restarted after a cold copy can receive newer writes; the backup is a
point-in-time copy. Perform a final quiesced delta before retiring live services
if writes continue. Live dev files use consistent SQLite copies separately.

## Plain Linux recovery

Mount the ext4 partition normally and read the backup's recovery/verification
notes first. Create users with matching IDs or explicitly remap ownership.
Restore dev's home/projects, tools and selected configuration onto a compatible
Linux install; do not blindly overwrite a new host's `/etc`, `/boot` or network
settings with Proxmox/guest-specific values. Use saved package lists as a guide.
Stop the relevant agent before applying its consistent SQLite copy, and remove
stale WAL/SHM sidecars only for that restored database. Preserve all encryption
keys alongside n8n, identity, OpenViking, Omni and other application databases.
Hardware-bound sign-in sessions may require normal reauthentication.

Install Docker/Compose, restore application directories and actual named-volume
contents, adapt paths/devices/networking, and start database dependencies before
apps. Prefer logical PostgreSQL exports across versions; raw data directories
require the same major version and compatible extensions. Existing image tags,
mount mappings and Compose files are recorded privately on the disk.

For Kubernetes, GitOps sources plus exported secrets/configuration and logical
application data support a fresh cluster or Docker deployment. Resource exports
include server-generated fields and must be reviewed before reapplying. Never
blindly restore an old etcd database into a different distribution/version.
Longhorn replicas alone are not a portable application-data backup.

## Availability and confidentiality

px30 is off/unreachable; its local-only filesystem data cannot be claimed backed
up. Current Kubernetes state and authoritative database data are accessible
through the surviving nodes. Its failed standby is not an independent source
for the current primary's logical data. The owner is attempting to revive it.

Backup contents include credentials and personal data. The mount and backup
root are root-only; nothing under this backup may be committed, uploaded to
Notion, published, or imported wholesale into agent memory. Publish only the
reviewed procedural summary. No destructive write touched internal source disks.
