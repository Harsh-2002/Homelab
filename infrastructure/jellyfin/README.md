# Jellyfin

Portainer stack 94 on `ctr` is the fresh Jellyfin instance. The old stack definition used LinuxServer.io, ran as root with `privileged: true`, referenced the erased `/EX` tree and an old domain, and was not running. The replacement uses the official Jellyfin 12.1 image pinned by digest, UID/GID 1000 with only the render GID 991 and `/dev/dri/renderD128`. No whole-GPU device, privileged mode, host networking, or automatic image updater is used.

| Purpose | Path |
| --- | --- |
| SMB library root | `/mnt/AV/media` on `ctr`, mounted read-only as `/media` |
| Movies | `/mnt/AV/media/movies` → `/media/movies` |
| TV Shows | `/mnt/AV/media/shows` → `/media/shows` |
| Unused staging folder | `/mnt/AV/media/source` → `/media/source` |
| Local app state | `/data/apps/jellyfin/config` → `/config` |
| Local cache and transcodes | `/data/apps/jellyfin/cache` → `/cache` |

Only the media subtree is presented to Jellyfin; `/mnt/AV/downloads` is not mounted into it. The two libraries are **Movies** (`/media/movies`) and **TV Shows** (`/media/shows`). `source` is not a library. The media bind is read-only so scans cannot modify source files. App state and transcoding cache stay on `ctr`'s local 500 GB ext4 `/data` disk, not the external SMB volume. The share itself is a single physical USB SSD and is not replicated.

The service listens on `10.1.1.4:8096` and Caddy exposes `https://media.l3b.cc.cd` publicly through an explicit DNS-only Cloudflare A record. Jellyfin retains its own application login; Caddy auth is not inserted in front of streaming clients. The administrator uses `iam.anuragvishwakarma@gmail.com`; its strong password is saved in the existing HomeLab 1Password `Jellyfin` item, scoped to this URL. No duplicate vault item was created.

Pocket ID OIDC uses the stable **Community SSO for Jellyfin** plugin 5.0.0.0 from Flowfin's release repository, configured by the tracked [`sso.json`](sso.json) copied to `/data/apps/jellyfin/config/sso.json`. The client ID is `jellyfin`, the callback is `https://media.l3b.cc.cd/sso/OID/redirect/pocketid`, and Pocket ID restricts access to `infrastructure-admins`. The confidential client secret is in the existing `Jellyfin` vault item's `oidc-client-secret` field and in `/data/apps/jellyfin/config/oidc-client-secret` on `ctr` (mode 0400, UID 1000); it is not in Git. The plugin reads the file through `OidSecretFile`. Its managed login-page button is enabled in the live plugin configuration and labelled **Sign in with Pocket ID**. Password login remains enabled as break-glass. Pocket ID itself is still private to LAN/Tailscale, so OIDC cannot finish from the open internet without Tailscale; the public Jellyfin password login can. Publishing Pocket ID would be a separate security decision.

The provider requests `openid`, `profile`, `email`, and `groups`, requires PKCE and a verified email for login/adoption, and maps `infrastructure-admins` to Jellyfin access and administrator rights. `DefaultUsernameClaim=email` is intended to link to the existing email-named administrator rather than create a second user. A real passkey sign-in and same-user-ID check are still required before calling account linking proven. Do not remove the local password until that has passed. Jellyfin has one `Name` field for both sign-in and display, so the app keeps the email as requested; the full name **Anurag Vishwakarma** is in Pocket ID and the existing vault item.

The plugin's hardened outbound transport normally refuses private IPs. Because `auth.l3b.cc.cd` intentionally resolves to the LAN proxy, this provider alone sets `AllowPrivateNetworkAddresses=true`; HTTPS, issuer, signature, and endpoint validation remain enabled. Jellyfin must also trust Caddy's forwarded protocol headers or it will construct an `http://` callback. Its live Network → Known Proxies contains `10.1.1.3` and the current `jellyfin_default` Docker bridge gateway `172.20.9.1`. Re-check that gateway after any network recreation. The old `Jellyfinn` vault item for Prabhat was deleted; it was not a Jellyfin server user.

Intel UHD 630 QSV was verified with a 10-frame H.264 hardware encode using the exact image, non-root UID and render group. Intel Quick Sync is enabled in Jellyfin with `/dev/dri/renderD128`, hardware encoding, and H.264/HEVC/VC-1/VP9 decoding. Verify an actual transcoding session in Jellyfin's playback and FFmpeg logs after media is added; the device test alone does not prove real playback.

The tracked `compose.yaml` is Portainer stack 94's source of truth. Update that stack in Portainer rather than starting a second Compose project. Before redeploying, confirm `findmnt -t cifs /mnt/AV` and its `seal` option. Verify the container is healthy and the Caddy URL loads after updating.
