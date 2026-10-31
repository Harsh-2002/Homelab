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
- `dev/consistent-sqlite/`: online SQLite backups of all detected Codex/OpenCode/Hermes
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
- `ctr/`: cold-copied ordinary Linux application files, bind data, named Docker
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
reviewed procedural summary. No internal source disk was formatted or erased.

For read-only integrity verification after moving the drive, run
`python3 manifests/verify-backup.py /path/to/homelab-backup-2026-10-31`.
Checksums cover regular-file bytes; symlink destinations and numeric ownership
are recorded in JSONL manifests. Successful copy/readback is not a full test
restore of every application on the future Linux host.

## 31 October transfer verification

The px10/dev phase completed before unplugging the drive: 1,283,749 manifest
entries and 266,411,806,985 bytes read back. All 14 consistent agent SQLite
copies passed integrity checks, selected critical source/configuration hashes
matched, and the unmounted filesystem checked clean. After attachment to px20,
the disk identity, selected hashes and all 14 databases were checked again.
The px20 USB-C link negotiated 10 Gbps.

CTR containers were stopped before copying. Application writers stopped before
fresh Immich/n8n logical PostgreSQL exports, then database containers stopped.
The copy includes 272,578,867,269 logical bytes under CTR data plus its root
configuration/projects; image caches are excluded. Saved private Docker inspect
and image-digest metadata describe all 30 containers, bind mounts and named
volumes. Previously running containers were restarted after the copy. Media
services and Watchtower remain deliberately stopped with the retired SMB layout.
The existing Gitea mirror restart loop is not resolved by this backup.

Home Assistant includes its unprotected application backup and extracted plain
configuration/add-on data. Orva's service was stopped for its file copy; its
SQLite database passed integrity checks. HAOS, Orva and proxy were temporarily
stopped during transfer and returned to their previous started requests.
`hosts-extra/` contains additional monitoring/host-local state. Original media
ownership may carry the old unprivileged LXC mapping; remap it to the new media
user when restoring. The backup ledger records final checksum completion.

px30 remains unavailable. Do not erase or sell its disks until its local-only
files are recovered or explicitly accepted as missing. Successful readback does
not establish that every service has been restored on the future Linux machine.

Phase-two checks passed for 22 cold SQLite databases, both gzip PostgreSQL
cluster exports (Immich and n8n), and all 52 mount sources referenced by the
30-container restore inventory. The phase-two service/host files produced
93,372 checksum entries and 11,170,373,612 bytes of readback. CTR bulk-data
readback is tracked separately in `ctr-data-files.progress.json`.

Home Assistant returned HTTP 200 and Orva returned its normal redirect after
restart. px20 retained cluster quorum and reported healthy ZFS pools during
readback. The separate px20 256 GB backup-store disk was inspected read-only
and is empty; the px10 256 GB ISO disk retains downloadable installer/template
files and was not erased. These separate disks are not the backup destination.

## Verified accessible-data handoff

All four data manifests completed: **1,616,613 files/links** and
**550,160,880,153 bytes read back**. CTR's 239,492 regular-file/symlink entries
match the completed rsync inventory exactly. The ext4 filesystem reported clean
after normal unmount on px20. The drive was remounted only to save the latest
committed Homelab repository and final recovery metadata, followed by another
normal unmount/filesystem check. Backup allocation is approximately457GiB;
logical byte counts include duplicated paths and sparse content.

`current-docs/Homelab/` preserves the latest repository separately from the
frozen dev copy. `manifests/STATUS.json` is the data verification ledger;
`DATA-MANIFESTS.sha256.json` seals the four data-manifest files. Additional
recovery-document checksums are recorded separately. The Notion runbook records
the final handoff and filesystem result.

This completes the accessible px10/dev and px20 backup scope. It does **not**
complete px30 local-only recovery, a new-host runtime restore, or any internal
source-disk erasure. Existing services may have written newer data after they
were restarted; preserve the source disks and take a quiesced delta if needed.

### OpenViking, Portainer and agent configuration

Verified persistent locations in the cold CTR data copy:

- OpenViking state: `ctr/data/apps/openviking/state/` (including its persisted
  memory/resources/index data and server configuration).
- OpenViking Ollama data: `ctr/data/apps/openviking/ollama/`.
- Portainer data: `ctr/data/portainer/`, including `portainer.db` and stack files.

The Docker socket is a runtime endpoint recreated by Docker, not backup data.
The dev copy contains `.ssh`, `.codex`, `.claude`, `.hermes`,
`.config/opencode` and `.openviking` under `dev/rootfs/home/dev/`, alongside
projects, other hidden configuration and system files. Agent SQLite recovery
copies have their own restore map. Database/configuration presence and checksum
readback do not replace a test startup on the future host.
