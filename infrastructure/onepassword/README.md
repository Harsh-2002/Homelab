# 1Password homelab secrets

The `HomeLab` vault is the authoritative store for application credentials, API tokens, recovery material, and automation secrets. An isolated service account gives the automation agent `read_items` and `write_items` only in this vault. It must not have access to personal vaults, item sharing, or vault creation.

Personal account items use one of two canonical identities: `iam.anuragvishwakarma@gmail.com` for email/OIDC logins and `iam-anuragvishwakarma` for username-only logins. Dotted and underscored username variants are retired. Machine identities such as `root`, `beszel`, and Kubernetes service accounts remain service-specific.

The service-account token is stored only on `dev` at `~/.config/op/service-account-token`, outside Git, with mode `0600`. Do not paste it into chat, commit it, export it globally, or add it to shell startup files.

Bootstrap once:

```bash
cd ~/Homelab
scripts/set-1password-service-token.sh
scripts/op-sa whoami
scripts/op-sa vault get HomeLab
```

Repository configuration may contain `op://HomeLab/item/field` references. Resolve them only for the process that needs them with `op run`, `op read`, or `op inject`. Never print a resolved value during validation.

Run Pocket ID reconciliation without a plaintext API-key file:

```bash
POCKET_ID_API_KEY="$(scripts/op-sa read 'op://HomeLab/Pocket ID Automation API/credential')" \
  scripts/configure-pocket-id-oidc.sh
```

Existing OIDC client secrets are stored as `Pocket ID OIDC - <client>` API Credential items. The reconciliation script creates a new secret file only when it creates an entirely new client; import that value into 1Password and remove the temporary file afterward.

## Managed current-state items

| Item | Purpose |
| --- | --- |
| `Beszel Monitoring` | Current user login and rotated break-glass password |
| `Beszel PocketBase Superuser` | PocketBase database break-glass account |
| `ArgoCD` | Local break-glass account, Pocket ID normal access, and the dedicated `Homepage` read-only API token |
| `Headlamp - K8s` | Permanent Kubernetes service-account token; Pocket ID is normal access |
| `AdGuard Home - DNS` | Native AdGuard administrator login |
| `Pocket ID` | Passkey identity metadata; no password stored |
| `Pocket ID Automation API` | Administrator API key used by automation |
| `Pocket ID OIDC - <client>` | Per-application OIDC client secret |
| `Pocket ID OIDC - portainer` | Portainer native Custom OAuth/OIDC client secret |
| `OpenCloud` | URL-specific login plus its bucket-scoped RustFS access key and secret |
| `Paperless-ngx` | URL-specific local break-glass login and retained `PAPERLESS_SECRET_KEY` |
| `Jellyfin` | URL-specific email/password login, full-name record, and Pocket ID OIDC client secret; the old `Jellyfinn` item was removed |
| `Pocket ID OIDC - paperless` | Paperless native OIDC client secret |
| `Portainer` | Native administrator login, the dedicated Homepage read-only API key, and an admin API access token for Stack management |
| `Cloudflare DNS API Token` | Caddy ACME DNS-01 token |
| `Proxmox` | Normal administrator login, plus the dedicated `Homepage` PVEAuditor API token |
| `Longhorn - K8s`, `Tinyauth` | Pocket ID access metadata; no application password stored |

Beszel and Argo CD break-glass passwords were generated in 1Password, applied to the live services, and verified with fresh logins. Portainer's restored local administrator remains a break-glass account while Pocket ID is its normal sign-in path. AdGuard and Headlamp credentials were validated against their live APIs. Redundant Pocket ID and Beszel credential files were removed from `dev` after byte-for-byte comparison and successful 1Password-backed reconciliation.

URLs formerly using the retired `*.ctl.qzz.io` domain were migrated to the equivalent `*.l3b.cc.cd` names. Credentials and usernames for inactive legacy applications are not changed until the corresponding service is restored and the identity migration can be verified end to end.

The service account is a privileged machine identity. Review its item-usage report, rotate its token periodically, and revoke it immediately if `dev` or an automation session is compromised. Creating a new account is required to change its immutable vault scope or permissions.
