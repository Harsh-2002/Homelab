# SMB share (Samba)

One authenticated SMB share, **`L3B`**, backed by `/data/apps/smb`. It is the
single media tree for the host: the share, Jellyfin, Motrix and qBittorrent all
read and write the same directories.

Set up 2026-11-04. Samba runs **natively**, not in Docker, so no container port
publication is involved and the daemon owns `/etc/samba` directly.

## Layout

```text
/data/apps/smb/
├── movies/       Jellyfin "Movies" library   (/media/movies)
├── shows/        Jellyfin "TV Shows" library (/media/shows)
├── downloads/    Motrix /downloads and qBittorrent /data/downloads
├── books/        empty, kept for the Jellyfin library
├── music/        empty, kept for the Jellyfin library
└── source/       empty scratch directory
```

Ownership is `dev:dev` (uid/gid 1000, setgid on the share root) because every
media container runs as `1000:1000`. Directory mode `2775`, files `0664`.

| Consumer | Host path | Container path |
| --- | --- | --- |
| SMB share `L3B` | `/data/apps/smb` | — |
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

## Connection details

| Field | Value |
| --- | --- |
| Server | `10.1.1.10` (or `l3b.l3b.cc.cd` from the LAN) |
| Share | `L3B` |
| User | `l3b` |
| Password | 1Password → `SMB L3B` |
| Protocol | SMB2 minimum, SMB3 negotiated |

macOS: Finder → Go → Connect to Server → `smb://10.1.1.10/L3B`.
Windows: Explorer → `\\10.1.1.10\L3B`.

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

[L3B]
   comment = L3B shared media
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
```

`nmbd` is disabled because NetBIOS is off; only **TCP 445** is used. `smbd` is
enabled at boot.

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
smbclient //127.0.0.1/L3B -U "l3b%$PW" \
  -c 'mkdir .t; put /etc/hostname .t/h; ls .t; del .t/h; rmdir .t'
unset PW
```

Expected: share list shows `L3B`, and the create/upload/list/delete cycle
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
