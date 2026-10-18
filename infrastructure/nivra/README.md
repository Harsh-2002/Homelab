# Nivra

## Agent MCP, verified 2026-10-18

The owner-provided access key now authenticates successfully at
`https://notes.l3b.cc.cd/mcp`. Global Codex, Claude Code and Hermes configurations
on dev contain the server named `nivra`; all three passed initialization and
discovery of97tools. Codex/Claude native config commands recognize the entry;
Hermes native MCP test connected and its gateway was gracefully reloaded.
New Codex/Claude sessions load the added server. Credentials are held only in
mode0600 local config files, with protected backups under
`~/.local/state/nivra-mcp-backups`. They are not stored in this repository or
memory. `configure-agent-mcp.py` takes a fresh owner key on stdin, preserves other
settings, refuses an existing entry and tests initialization/discovery. The
older failed-MCP-credential statements below are superseded; native UI password
login remains separately unverified.

Nivra **v2026.10.16**, commit `8a761e26728f6a5ccb6bd97cce29acd96beb05e2`, is deployed on `ctr` as Portainer stack **157**, `nivra` (endpoint2). At the owner's explicit request, the Compose image is **`ghcr.io/harsh-2002/nivra:latest`**, without a digest pin. The image observed during this upgrade matches the published release. CI run38905049889 succeeded for that exact release commit. No upstream release/tag/CI settings were modified. Caddy access policy and DNS were left unchanged: existing private LAN/Tailscale route at `https://notes.l3b.cc.cd`.

## October18 IST upgrade acceptance

- Pre-pulled the replacement while the old container served requests, then upgraded through the Portainer API, not an unmanaged Docker replacement.
- Stopped the application writer for a consistent full-directory backup at **`/data/nivra-upgrade-backups/20261017T230737Z/data.tar.gz`**. Root-only directory0700/archive0600; saved previous Portainer stack/environment alongside it. SQLite integrity and every archive member were checked before deployment.
- New image uses the same `/data/apps/nivra` bind mount, port3020, encryption setting and proxy. No VM restart, data reset or unrelated service changes.
- Container healthy; HTTPS `/health`200; unauthenticated notes and MCP denied. Browser login surface loads. Both extension migrations0054/0055 are present.
- All11 checked existing tables, including owner, note, attachments, tasks, bookmarks, artifacts, forms and API-key/OAuth-client data, have identical row counts and content hashes after migration. Encryption key/mode, auth secret and installation metadata are byte-identical to the backup. No private contents or credential values were printed.
- **Native owner login could not be verified:** the existing HomeLab→Nivra login returned401 before the upgrade. No password reset, MFA bypass or account change was attempted. `validate.py` reproduces the read-only owner-login check using the protected vault credential. Authenticated UI/MCP operations need the correct existing credential; do not claim these were tested.
- Prior image retained for rollback. If migrations make a downgrade incompatible, stop Nivra and restore the consistent pre-upgrade data plus previous stack together; do not blindly run an older binary against migrated data. Backup restore itself was not drilled.
- `latest` is mutable. Record runtime version/commit on each update; a tag in Compose does not automatically pull new releases by itself. Run the controlled Portainer update after backup. No automatic updater was added.

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

For upgrades, read the exact release notes and pre-pull the official `latest` image, then use `python3 infrastructure/nivra/upgrade.py` from dev. It obtains the Portainer operator key without printing it, locates the existing stack, preserves its environment, stops the writer, creates/checks the backup and deploys the tracked Compose through Portainer. It refuses missing images or ambiguous stack identity. Keep the data directory and verify actual image release/commit, health, native login, note/attachment persistence and MCP access afterward. Use `latest` without a SHA pin per the owner's October18 instruction, superseding the original digest-pinning policy.

Sources: [v2026.10.16 release](https://github.com/Harsh-2002/Nivra/releases/tag/v2026.10.16), [verified CI](https://github.com/Harsh-2002/Nivra/actions/runs/38905049889), [tagged README](https://github.com/Harsh-2002/Nivra/blob/v2026.10.16/README.md), [tagged architecture and recovery](https://github.com/Harsh-2002/Nivra/blob/v2026.10.16/docs/architecture.md).
