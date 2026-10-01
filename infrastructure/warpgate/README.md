# Warpgate remote access

Warpgate 0.29.1 runs on ctr in Portainer stack `warpgate` (ID 156, endpoint 2). Its core is Rust with a bundled Svelte/TypeScript web UI. Private endpoint: https://remote.l3b.cc.cd. The existing Caddy proxy terminates the external certificate and verifies the HTTPS backend at `10.1.1.4:8091` against `upstream-ca.pem`, installed as `/etc/caddy/warpgate-upstream.pem`. No certificate-verification bypass is used. Access retains Caddy's LAN/Tailscale-only policy.

## State and security

`compose.yaml` is the sanitized Portainer Stackfile. All state, SQLite database, SSH keys, TLS key/certificate and configuration persist in `/data/apps/warpgate`, mounted at `/data`. The directory is owned by 1000:1000 with mode 0700; secret configuration and keys are mode 0600. Preserve both state and encryption key together when backing up or restoring.

The official pinned image runs non-root with a read-only root filesystem, writable temporary `/tmp`, no-new-privileges, dropped capabilities, bounded logs and Watchtower opt-out. Its own default Docker bridge is used. No docknet, Docker socket, external database or additional proxy. HTTP is published only on the ctr LAN address; native SSH port 2222 is internal and not published. RDP/VNC and other optional protocol listeners are disabled. Limits: 512 MiB and one CPU. Revisit limits if concurrent usage demonstrates pressure.

HomeLab vault item `Warpgate` contains the owner password, encryption key and Pocket ID client secret. The only permanent Compose variable is `WARPGATE_ENCRYPTION_KEY`, a base64-encoded 32-byte key. `config.example.yaml` is a sanitized example, not the runtime secret configuration.

## Authentication

Owner: `iam.anuragvishwakarma@gmail.com`, display name Anurag Vishwakarma. The initial admin was renamed rather than creating a second owner. Its Pocket ID SSO credential is linked by provider `pocketid` and the same email. Auto-creation of users is disabled. Pocket ID client `warpgate` is confidential with PKCE and restricted to `infrastructure-admins`. Callback: `https://remote.l3b.cc.cd/@warpgate/api/sso/return`.

Temporary bootstrap admin access was removed from the running command/environment and its temporary token was deleted from the vault. It is not a permanent client API key.

## Verification and pending work

Verified: container starts cleanly, private Caddy route serves the Warpgate login, upstream TLS verification works, official favicon returns HTTP 200 as SVG, owner identity and SSO credential persist in SQLite. Browser SSH target provisioning and a complete owner passkey sign-in remain pending. A restricted dedicated Warpgate public key was appended to dev's `authorized_keys`; no dev private key was copied. Target host keys must be pinned from trusted existing SSH sessions, not accepted automatically. Do not report browser sessions functional until an actual target session has been tested.

## Termix decommission, 2026-10-01

At the owner's explicit request, Portainer stack `termix` (155) and its `termix`/`guacd` containers were deleted through the Portainer API. No remaining container references its data directory. Deleted `/data/apps/termix`, both unused images, its HomeLab vault item and active manifests. Homepage and Caddy now refer only to Warpgate. The deleted host data is not recoverable through this cleanup; the vault item remains subject to 1Password's deleted-item retention. Git history preserves historical configuration, not active deployment files.

Sources: [official Docker deployment](https://warpgate.null.page/getting-started-on-docker/), [SSO](https://warpgate.null.page/sso/), [reverse proxy](https://warpgate.null.page/reverse-proxy/), [SSH targets](https://warpgate.null.page/targets/ssh/), [v0.29.1 source](https://github.com/warp-tech/warpgate/tree/v0.29.1).
