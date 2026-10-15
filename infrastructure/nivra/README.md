# Nivra

Nivra v2026.10.15 is deployed on `ctr` as the Portainer stack `nivra` (endpoint 2). It uses the official multi-architecture image pinned to release commit `b52a1d7` and digest `sha256:fdcb28a35356ab57257ab4e9ffc705840913dcb64bf6f2cb6ddeca3391ad781d`. Nivra is staged at `https://notes.l3b.cc.cd` behind Caddy's private LAN/Tailscale policy until the owner completes first-run setup. Do not publish its Cloudflare record before creating the owner.

## Runtime and persistence

This is one container with Nivra's supported SQLite storage; it has no external database or cache. Portainer binds only `10.1.1.4:3020` on CTR's LAN interface to container port 3000. Caddy proxies the HTTPS hostname to that address. The Docker health check calls `/health`.

All durable application state is bind-mounted from `/data/apps/nivra` to `/data`. The host directory must be owned by UID/GID 1000, matching the unprivileged image user. Keep this directory for upgrades and container recreation. Nivra config, SQLite, uploads, local keys, and recovery metadata live there.

## Encryption and authentication

The owner requested no encryption at rest. The stack sets `NIVRA_ENCRYPTION_ENABLED=false` before the first startup; Nivra persists that choice for the installation. Notes, SQLite and uploaded files are therefore plaintext on CTR's disk. Authentication secrets and exported application backups remain encrypted by Nivra. No external encryption key is mounted. Do not change this setting after the installation has initialized.

Nivra has one owner and native password/passkey authentication; public sign-up is disabled. It does not use the Anchor Pocket ID client or Tinyauth. Complete first-run account setup at the HTTPS hostname while it is still private. Verify the UI reports encryption disabled and store the one-time recovery code securely. Only then change the Nivra Caddy handler to public access and create the explicit DNS-only Cloudflare A record `notes.l3b.cc.cd -> 150.129.31.154`. Leave the Caddy origin on the LAN and preserve the internal Unbound answer `10.1.1.3`. Confirm an unauthenticated remote request reaches Nivra's login/setup protection and that private API content is not returned.

The previous Anchor service remains running as Portainer stack `anchor`, at the private alias `https://anchor.l3b.cc.cd`, with its original data in `/data/apps/anchor`. Its Pocket ID client and Homepage entry are kept separate.

## Operations

Inspect the deployed stack in Portainer or check it from CTR:

```sh
ssh ctr 'docker inspect nivra --format "{{.State.Health.Status}} {{.State.OOMKilled}}"'
curl -fsS https://notes.l3b.cc.cd/health
```

Before an upgrade or recovery, use Nivra's application backup and retain a consistent copy of `/data/apps/nivra`. Because at-rest encryption is disabled, filesystem-level copies contain plaintext notes and uploads; protect backups accordingly. Do not copy the live SQLite directory while the application is writing to it.

For upgrades, read the exact release notes, take and validate a backup, then pin the new official release digest in this file and the Portainer stack together. Keep the existing data directory. Verify health, native login, note and attachment persistence, and MCP access after each upgrade.

Sources: [v2026.10.15 release](https://github.com/Harsh-2002/Nivra/releases/tag/v2026.10.15), [tagged README](https://github.com/Harsh-2002/Nivra/blob/v2026.10.15/README.md), [tagged architecture and recovery](https://github.com/Harsh-2002/Nivra/blob/v2026.10.15/docs/architecture.md).
