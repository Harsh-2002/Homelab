# Pocket ID

Pocket ID runs as a pinned standalone Go binary under systemd in Proxmox CT 103. Docker is intentionally not installed.

## Topology

| Item | Value |
| --- | --- |
| Guest | `auth` / CT 103 |
| Primary node | `px30` |
| HA target | `px10` |
| Replication | `103-0`, every 5 minutes |
| Address | `10.1.1.6` |
| URL | `https://auth.l3b.cc.cd` |
| Resources | 1 vCPU, 1 GiB RAM, 512 MiB swap |
| Root disk | 10 GiB `local-zfs` |
| Runtime | systemd, unprivileged Debian 13 LXC |
| Service port | `1411/tcp` |
| Database | local SQLite |

Pocket ID v2 is single-instance software. Availability comes from Proxmox HA restarting CT 103 on another node; do not start a second Pocket ID process against the same database.

The strict `ct103-replica-nodes` HA affinity rule permits only `px30` and `px10`, with `px30` preferred. A controlled relocation to `px10` and back was completed successfully on 2026-09-20 while the HTTPS endpoint remained healthy.

## Access

Root administration is allowed only with the shared Ed25519 SSH key. The root password is locked, and SSH password and keyboard-interactive authentication are disabled. Pocket ID itself runs as the unprivileged `pocket-id` system account.

Complete first-run enrollment from the private network at:

```text
https://auth.l3b.cc.cd/setup
```

Register the primary passkey in 1Password and keep a second recovery passkey before connecting other services.

## Paths

- Binary symlink: `/usr/local/bin/pocket-id`
- Versioned binaries: `/opt/pocket-id/versions/`
- Environment: `/etc/pocket-id/pocket-id.env`
- Sanitized environment template: `pocket-id.env.example`
- Encryption key: `/etc/pocket-id/encryption-key`
- Database and uploads: `/var/lib/pocket-id/`
- Unit: `/etc/systemd/system/pocket-id.service`
- Upgrade helper: `/usr/local/sbin/pocket-id-upgrade`
- SSH policy: `/etc/ssh/sshd_config.d/10-key-only.conf`

The encryption key and application data must be backed up together. Neither belongs in Git or Notion.

## Operations

```bash
systemctl status pocket-id
journalctl -u pocket-id -f
systemctl restart pocket-id
```

## Tinyauth

Tinyauth v5.2.0 runs in the same container as a separate systemd service and provides Caddy forward authentication for applications without native OIDC. Its public endpoint is `https://login.l3b.cc.cd`; Homepage, Longhorn, AdGuard Home, Frigate, and Uptime Kuma are protected by the `infrastructure-admins` Pocket ID group.

Tinyauth uses the global `deny` ACL policy. Each protected application therefore has both an explicit OAuth email whitelist and the required `infrastructure-admins` group. In Tinyauth v5 these are separate checks: the application whitelist must allow the user before the OAuth group rule is evaluated.

Because Pocket ID and Tinyauth share CT 103, `/etc/hosts` explicitly resolves `auth.l3b.cc.cd` to the Caddy proxy at `10.1.1.3`. This is required for Tinyauth's server-side OAuth token exchange; resolving the public name to CT 103 itself would connect to an unused local port 443.

```bash
systemctl status tinyauth
journalctl -u tinyauth -f
getent ahostsv4 auth.l3b.cc.cd
```

The final command must return `10.1.1.3`.

### Identity integrations

| Service | Integration | Authorization |
| --- | --- | --- |
| Headlamp | Native OIDC | Pocket ID group `infrastructure-admins` maps to Kubernetes `cluster-admin` |
| Argo CD | Native OIDC | Pocket ID group `infrastructure-admins` maps to `role:admin`; local named account remains break-glass |
| Proxmox | Native OIDC realm `pocketid` | PVE group `infrastructure-admins` has `Administrator` at `/`; PAM/local access remains break-glass |
| Proxmox Backup Server | Native OIDC realm `pocketid` | PBS user `iam.anuragvishwakarma@gmail.com@pocketid` has `Admin` at `/`; `root@pam` remains break-glass; browser passkey return awaits owner verification |
| Memos | Native OAuth2 provider `pocketid` | Provider is group-restricted; the existing local account has not yet linked its Pocket identity, and Memos is under replacement review |
| Portainer | Native Custom OAuth/OIDC | Pocket ID client `portainer`; automatic user provisioning enabled; local Portainer administrator remains break-glass |
| Karakeep | Native OIDC | Client is restricted to `infrastructure-admins`; existing Karakeep account is linked by the verified canonical email; native Karakeep login remains break-glass |
| Immich | Native OIDC | Client `immich` is restricted to `infrastructure-admins`; the pre-existing photo account is explicitly linked and native login remains break-glass |
| OpenCloud | Native public-client OIDC with PKCE | Web, desktop, Android, and iOS clients are restricted to `infrastructure-admins`; its `opencloud_role` claim grants `opencloudAdmin` |
| Paperless-ngx | Native OIDC | Client `paperless` is restricted to `infrastructure-admins`; Paperless maps that group claim to superuser status and retains a separate local break-glass login |
| AdGuard Home | Caddy forward auth through Tinyauth | Exact OAuth email whitelist and required `infrastructure-admins` group |
| Longhorn | Caddy forward auth through Tinyauth | Exact OAuth email whitelist and required `infrastructure-admins` group |
| Homepage | Caddy forward auth through Tinyauth | Exact OAuth email whitelist and required `infrastructure-admins` group |
| Uptime Kuma | Caddy forward auth through Tinyauth | Exact OAuth email whitelist and required `infrastructure-admins` group; built-in auth is disabled and nftables restricts the backend to Caddy |

Pocket ID emits the user-group friendly name in the OIDC `groups` claim. Both the machine name and friendly name are therefore set to `infrastructure-admins`, matching every downstream RBAC rule. That group also emits the application-specific `opencloud_role=opencloudAdmin` claim. The idempotent client/group provisioning script is `scripts/configure-pocket-id-oidc.sh`. Generated client secrets remain outside Git and Notion; OpenCloud public PKCE clients have no client secrets.

Tinyauth's global ACL policy is `deny`. Provider-level OAuth whitelisting permits creation of a login session, while each application's `oauth.whitelist` and `oauth.groups` are independent authorization checks. A protected application needs both entries. The known-good session exposes:

```text
Remote-User: iam-anuragvishwakarma
Remote-Email: iam.anuragvishwakarma@gmail.com
Remote-Groups: infrastructure-admins
```

### Kubernetes API OIDC

Talos applies `talos-k8s/oidc.patch.yaml` as a `KubeAuthenticationConfig`. The API server trusts issuer `https://auth.l3b.cc.cd` for audience `headlamp`, maps `preferred_username` with prefix `oidc:`, maps groups with prefix `oidc:`, and maps `sub` as the UID. The `oidc:infrastructure-admins` ClusterRoleBinding grants `cluster-admin`.

Structured API authentication no longer inherits the former `system:masters` behavior for `apiserver-kubelet-client`. A narrow binding to the built-in `system:kubelet-api-admin` role restores pod logs and node proxy access without granting unrelated cluster administration.

### Troubleshooting history

- Tinyauth token exchange initially failed because CT 103 resolved `auth.l3b.cc.cd` to itself at `10.1.1.6:443`. The container now resolves that public name through Caddy at `10.1.1.3`.
- An empty provider whitelist rejected the Pocket ID email before a Tinyauth session could be created. The provider now explicitly permits the administrator email.
- A group-friendly-name mismatch was removed by standardizing it to `infrastructure-admins`.
- With ACL policy `deny`, per-app OAuth whitelists are mandatory even when the group claim matches. DNS and Longhorn now require both the exact email and group.

Validate the two forward-auth applications with a browser session and confirm an unauthenticated CLI request receives `401`, not direct backend content:

```bash
curl -I https://dns.l3b.cc.cd
curl -I https://longhorn.l3b.cc.cd
```

## Upgrade

Read the release notes and migration guide, then pass an explicit release tag:

```bash
sudo pocket-id-upgrade v2.16.0
```

The helper downloads the official Linux AMD64 binary and published checksums, verifies SHA-256 before stopping the service, installs into a versioned directory, and restores the previous binary if startup fails. Never use an unpinned `latest` URL in automation.

After an upgrade:

```bash
systemctl is-active pocket-id
journalctl -u pocket-id --since '-5 minutes'
curl --fail --silent https://auth.l3b.cc.cd/ >/dev/null
```

## Backup and recovery

Proxmox replication is availability, not backup. Maintain scheduled Proxmox backups and an application-consistent copy of `/var/lib/pocket-id` plus `/etc/pocket-id/encryption-key`. Retain local break-glass credentials for Proxmox and Kubernetes in case the identity provider is unavailable.
