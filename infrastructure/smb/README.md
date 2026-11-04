# SMB share (Samba)

Two authenticated SMB shares, **`MEDIA`** and **`BACKUP`**. `MEDIA` is backed by `/data/apps/smb` and is the
single media tree for the host: the share, Jellyfin, Motrix and qBittorrent all
read and write the same directories.

Set up 2026-11-04. Samba runs **natively**, not in Docker, so no container port
publication is involved and the daemon owns `/etc/samba` directly.

## Layout

```text
/data/apps/smb/
├── movies/       Jellyfin "Movies" library   (/media/movies)
├── shows/        Jellyfin "TV Shows" library (/media/shows)
└── downloads/    flat download target for Motrix and qBittorrent
```

Ownership is `dev:dev` (uid/gid 1000, setgid on the share root) because every
media container runs as `1000:1000`. Directory mode `2775`, files `0664`.

| Consumer | Host path | Container path |
| --- | --- | --- |
| SMB share `MEDIA` | `/data/apps/smb` | — |
| Jellyfin | `/data/apps/smb` | `/media` |
| Motrix | `/data/apps/smb/downloads` | `/downloads` |
| Motrix (media) | `/data/apps/smb` | `/media` |
| qBittorrent | `/data/apps/smb` | `/data` |

Jellyfin's own configuration and cache stay at `/data/apps/jellyfin/{config,cache}`;
only the libraries point at the shared tree.

## Authentication and permissions

- Samba user **`l3b`** (system account, uid 986, no shell, no home).
- Password is the `password` field of the 1Password item **`SMB L3B`** in the
  `HomeLab` vault. It is never stored in Git or the Compose files.
- `force user = dev` / `force group = dev`: every file operation on the share runs
  as the same uid/gid the media containers use, so a file created from macOS or
  Windows is immediately readable and writable by Jellyfin, Motrix and
  qBittorrent.
- macOS AppleDouble files (`._*`) and `.DS_Store` are vetoed and removed with the
  parent directory.

## Discovery (Bonjour / mDNS)

`avahi-daemon` is installed and restricted to `eno1`
(`allow-interfaces=eno1` in `/etc/avahi/avahi-daemon.conf`) so it does not
advertise on Docker bridges. Samba registers with it automatically
(`multicast dns register = yes`, the default).

What macOS and Windows see:

| Record | Meaning |
| --- | --- |
| `_smb._tcp` on `l3b.local:445` | the server appears in Finder/Explorer network browse |
| `_adisk._tcp` with `dk0=adVN=BACKUP` | **BACKUP** is offered to Time Machine as a destination |

Only `BACKUP` carries `fruit:time machine = yes`, so Time Machine lists one
choice, not both. `MEDIA` is never offered as a backup target.

Consequences for clients:

- Finder → **Connect to Server** → `smb://smb.l3b.cc.cd`, `smb://10.1.1.10` or `smb://l3b.local`,
  authenticate once, then pick `MEDIA` or `BACKUP` from the list.
- Time Machine → **Add Backup Disk** shows `BACKUP` automatically; no manual
  `tmutil` command is needed while Avahi is running.
- Windows → `\\smb.l3b.cc.cd` lists both shares after one login.

Verify with:

```sh
avahi-browse -rt _smb._tcp
avahi-browse -rt _adisk._tcp
```

## Connection details

| Field | Value |
| --- | --- |
| Server | **`smb.l3b.cc.cd`** (or `10.1.1.10`, or `l3b.local` via mDNS) |
| Shares | `MEDIA` (media) and `BACKUP` (backups) |
| User | `l3b`, the same account and password for **both** shares |
| Password | 1Password → `SMB L3B` |
| Protocol | SMB2 minimum, SMB3 negotiated |

macOS: Finder → Go → Connect to Server → `smb://smb.l3b.cc.cd/MEDIA`.
Windows: Explorer → `\\smb.l3b.cc.cd\MEDIA`.

## Configuration

`/etc/samba/smb.conf` (the packaged original is kept as `smb.conf.orig`):

```ini
[global]
   workgroup = WORKGROUP
   server string = l3b
   security = user
   map to guest = never
   server min protocol = SMB2
   disable netbios = yes
   smb ports = 445
   unix charset = UTF-8
   log file = /var/log/samba/log.%m
   max log size = 1000
   logging = file
   panic action = /usr/share/samba/panic-action %d
   obey pam restrictions = yes
   unix password sync = no
   usershare allow guests = no
   load printers = no
   printing = bsd
   printcap name = /dev/null
   disable spoolss = yes

[MEDIA]
   comment = L3B media library
   path = /data/apps/smb
   browseable = yes
   read only = no
   guest ok = no
   valid users = l3b
   force user = dev
   force group = dev
   create mask = 0664
   directory mask = 2775
   veto files = /._*/.DS_Store/
   delete veto files = yes
   vfs objects = fruit streams_xattr
   fruit:metadata = stream
   fruit:model = MacSamba
   fruit:posix_rename = yes
   fruit:veto_appledouble = yes
   fruit:copyfile = yes
   fruit:nfs_aces = no
   use sendfile = yes
   aio read size = 1
   aio write size = 1
```

`nmbd` is disabled because NetBIOS is off; only **TCP 445** is used. `smbd` is
enabled at boot.

## Second share: `BACKUP`

Added 2026-11-04 on a separate 1.92 TB Seagate Nytro XF1230 SSD in a VIA VL817
USB enclosure.

| Item | Value |
| --- | --- |
| Disk | Seagate Nytro XF1230 1.92 TB, serial `7CX01767` |
| Connection | Rear USB-A, 5000 Mbps |
| Filesystem | ext4, label `BACKUP`, UUID `ade7d423-6a2d-4f5b-800d-cba5c027d770` |
| Mount | `/BACKUP` (fstab, `nofail`) |
| Share | `BACKUP`, `fruit:time machine = yes`, no size cap |
| Owner | `dev:dev`, mode `2775` on the mount root |

This disk is deliberately **not** under `/mnt`. It is the Time Machine and
homelab-backup target; `MEDIA` stays media-only. Time Machine has no size cap, so
it can consume the whole 1.8 TB; delete old snapshots in System Settings if
space runs low.

### USB link findings

| Port | Negotiated | Driver | 10 GiB read |
| --- | --- | --- | --- |
| Front USB-A | 5000 Mbps | `usb-storage` | 373 MiB/s |
| Front USB-A | 5000 Mbps | `uas` | **392 MiB/s** |
| Rear USB-A | 5000 Mbps | `uas` | **392 MiB/s** |
| Front USB-C | **480 Mbps** | `usb-storage` | 41 MiB/s |

The Type-C port fell back to USB 2.0 with the cable used; it is unusable for
backups. The rear USB-A port matches the front and is the permanent connection.

The VL817 bridge is blacklisted from UAS by the kernel
(`UAS is ignored for this device`). `usb-uas-rebind.sh` plus a udev rule forces
the faster driver on every attach:

```text
/usr/local/sbin/usb-uas-rebind.sh
/etc/systemd/system/usb-uas-rebind.service
/etc/udev/rules.d/90-vl817-uas.rules
```

The script resolves the interface symlink before reading `idVendor`, unbinds
`usb-storage`, binds `uas`, and falls back to `usb-storage` if that fails.
Verified by forcing `usb-storage` and re-running the script.

Write cache is reported disabled by the bridge, so write throughput is lower
than read. Local `dd` to `/BACKUP` measured 387 MB/s.

## Verification

```sh
sudo testparm -s
systemctl status smbd --no-pager
ss -ltn | grep ':445'
```

Write test with the real credentials (password read from 1Password, never typed
into a file):

```sh
export OP_SERVICE_ACCOUNT_TOKEN=$(cat ~/.config/op/service-account-token)
PW=$(op item get "SMB L3B" --vault HomeLab --fields password --reveal)
smbclient //127.0.0.1/MEDIA -U "l3b%$PW" \
  -c 'mkdir .t; put /etc/hostname .t/h; ls .t; del .t/h; rmdir .t'
unset PW
```

Expected: share list shows `MEDIA` and `BACKUP`, and the create/upload/list/delete cycle
returns no errors.

## Recreating this setup

```sh
sudo apt-get install -y samba smbclient
sudo useradd --system --no-create-home --shell /usr/sbin/nologin l3b
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.orig
sudo tee /etc/samba/smb.conf   # paste the configuration above
sudo testparm -s
sudo smbpasswd -a l3b          # password from 1Password → SMB L3B
sudo systemctl enable --now smbd
sudo systemctl disable --now nmbd
```

## Limits

- SMB is unencrypted at rest on the wire beyond SMB3 transport encryption; it is
  a LAN share, not a remote-access service. Do not port-forward 445.
- The host firewall is Docker's NAT only; 445 is reachable from anything that can
  route to `10.1.1.10`.
- No quotas are configured; the share is limited only by `/data`.
- The share grants whatever `dev` can do inside `/data/apps/smb`. Keep only media
  and downloads there.


## macOS compatibility (vfs_fruit)

`vfs objects = fruit streams_xattr` stores Finder metadata in xattrs instead of
`._*` sidecar files, gives Finder a proper icon, enables server-side copy and
uses POSIX renames. It requires xattr support, which XFS has — verified with a
`user.test` xattr round trip on `/data`.

## Performance

Measured 2026-11-04 with a 1 GiB file over loopback:

| Path | Before tuning | After |
| --- | --- | --- |
| SMB write | 450 MB/s | **467 MB/s** |
| SMB read | 1245 MB/s | **1381 MB/s** |
| Raw XFS write (`dd` + fsync) | — | 443 MB/s |
| Raw XFS read (`dd` iflag=direct) | — | 481 MB/s |

Samba already reaches the SSD's own write speed, so the share is not the
bottleneck. `use sendfile`, `aio read size = 1` and `aio write size = 1` are set
for asynchronous I/O on every request size.

Real-world copies are limited by the **1 GbE** link (`eno1` reports 1000 Mb/s),
i.e. roughly 110–118 MB/s per client. Ten-gigabit or 2.5 GbE is the only way to
go faster; no Samba setting will change that. Jumbo frames are not enabled
because the switch and client support is not guaranteed.

## DNS name

`smb.l3b.cc.cd` is an exact **DNS-only A record to 10.1.1.10**, in Cloudflare and
resolvable from the LAN. It replaces the old stale record that pointed at the
retired `10.1.1.12`. Port 445 is not forwarded, so the name resolves publicly to a
private address and the service stays LAN-only.

Clients may use any of: `smb.l3b.cc.cd`, `10.1.1.10`, or `l3b.local` (mDNS).
Prefer the DNS name — it survives an address change.

## Changing the password

Both shares authenticate as the single Samba user `l3b`, so one command changes
the password everywhere:

```sh
sudo smbpasswd l3b
```

It prompts twice for the new password, writes the tdbsam entry and takes effect
immediately — no restart. Devices with the share already mounted keep their
session until they disconnect; remount or reboot them to force re-authentication.

Then update the `password` field of the 1Password item `SMB L3B` so the record
matches.

`pdbedit -L` lists the Samba accounts; `sudo smbpasswd -a l3b` adds the account
if it is ever missing.

## Internal SATA vs this USB disk

Both disks are the same model, Seagate Nytro XF1230 1.92 TB, so only the bus
differs: internal SATA 6.0 Gb/s against USB 5 Gbps with UAS.

| Test | SATA `/data` | USB `/BACKUP` | USB vs SATA |
| --- | --- | --- | --- |
| Raw 10 GiB read, `O_DIRECT` | 472 MiB/s | 387 MiB/s | **−18%** |
| 1 GiB file write + `fdatasync` | 425 MiB/s | 389 MiB/s | −8% |
| 1 GiB file read, `O_DIRECT` | 443 MiB/s | 350 MiB/s | −21% |

The USB path is roughly 80% of direct SATA and tops out near 390 MiB/s, which is
the 5 Gbps link, not the SSD. A 10 Gbps enclosure would not help much either:
this SATA SSD peaks around 480 MiB/s.

Neither number matters for SMB clients — the 1 GbE LAN caps them at ~110 MiB/s.
The difference is only visible for local work such as writing a backup directly
to `/BACKUP`.

## If a client suddenly gets LOGON_FAILURE

Samba can keep a password hash that no longer matches the 1Password item, and
the server then logs `NT_STATUS_WRONG_PASSWORD` in `/var/log/samba/log.<client>`
even though `pdbedit -L` shows the account fine. Re-apply the stored value:

```sh
export OP_SERVICE_ACCOUNT_TOKEN=$(cat ~/.config/op/service-account-token)
PW=$(op item get "SMB L3B" --vault HomeLab --fields password --reveal)
printf '%s\n%s\n' "$PW" "$PW" | sudo smbpasswd -a -s l3b
```

Confirmed to survive `systemctl restart smbd` and `reload`. Raising
`log level = 3` shows the exact failure reason in the per-client log.

## Folder policy

Only three directories exist at the share root: `movies`, `shows`, `downloads`.
The earlier `books/`, `music/` and `source/` folders and the per-category
subfolders under `downloads/` were removed on 4 November 2026 at the owner's
request. `downloads/` is intentionally flat: Motrix saves directly to
`/downloads`, and qBittorrent's default save path is `/data/downloads`.

Jellyfin's **Music** library was removed on 4 November 2026 together with the
`music/` folder, so no scan warns about `/media/music` any more. Only the
**Movies** and **TV Shows** libraries remain.
