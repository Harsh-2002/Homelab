# Nivra: The King

Separate friend-owned instance deployed 2026-10-19. This is not a second account
inside the owner's Nivra and does not share its data, settings or credentials.

| Item | Value |
| --- | --- |
| Public URL | https://theking.l3b.cc.cd |
| Host | CTR 10.1.1.4 |
| Portainer stack | nivra-theking, ID159, endpoint2 |
| Container | nivra-theking |
| Origin listener | 10.1.1.4:3021 to container3000 |
| Persistent data | /data/apps/nivra-theking mounted at /data |
| Image | ghcr.io/harsh-2002/nivra:latest |
| Observed release | v2026.10.16, commit8a761e2 |

Existing Caddy serves the hostname publicly, without Tinyauth or a private-source
gate. Native Nivra authentication protects private content and MCP. Cloudflare
DNS-only A record is the household WAN address150.129.31.154. Internal DNS retains
the existing wildcard route to Caddy10.1.1.3. The raw application port remains
bound to CTR's LAN address; no new router forwarding was added.

## Friend performs onboarding

The owner explicitly requested **no account creation**. No owner email, username,
password, recovery code, API key, agent configuration or Homepage entry was made.
The friend completes the standard wizard at the public URL and chooses their
identifier, authentication and encryption. Encryption is deliberately not forced
off by the deployment; it defaults on unless the friend chooses otherwise.

**An unclaimed public installation can be claimed by its first visitor.** The
friend should complete onboarding promptly and retain their recovery code.
Do not initialize an owner or read private content on their behalf. Public signup
is disabled after the one-owner setup. Preserve the generated installation data
and keys after onboarding; never copy the primary Nivra's directory over this one.

## Deployment and verification

Source: docker-compose.yaml. Creation is through the existing Portainer API:

```bash
python3 infrastructure/nivra-theking/deploy.py
```

The helper resolves the existing Portainer operator credential through HomeLab
1Password without printing it, refuses existing stack/data targets, creates an
independent UID/GID1000 data directory and deploys only the new stack. It waits
for healthy status, tolerating Docker's brief container-not-yet-created404 after
Portainer's asynchronous stack response. It does not pull/recreate the original
Nivra, onboard a user or change DNS/proxy automatically.

Checks performed: Portainer stack159 healthy; correct independent RW bind mount
and unprivileged UID1000; private raw port3021; existing notes container healthy
and untouched; Caddy config validation and graceful reload; recursive public DNS
returns WAN IP; valid HTTPS and health200 through that IP; browser displays setup
step1 with name/identifier fields; status reports setup required and no owner;
notes/system APIs and MCP initialize401 without authentication. No signup or
login was submitted. The database is intentionally not opened/created before
onboarding chooses encryption, so an empty directory at this stage is normal.

WAN-address testing was from inside home, not an independent off-network probe.
Authenticated operations, persisted notes and recovery remain untested until the
friend creates their account. No false claim of full post-onboarding acceptance.

Keep all future upgrades Portainer-managed with the same data mount. Back up the
complete data consistently before upgrading; the current deploy helper is
create-only, not an upgrade command. Do not point the primary instance's upgrade
helper at this separate stack without adapting its exact-target checks.

Official release instructions:
https://github.com/Harsh-2002/Nivra/tree/v2026.10.16
