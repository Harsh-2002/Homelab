# Anchor notes

Anchor v0.17.2 runs on `ctr` in Portainer stack `anchor` (ID 154, endpoint 2). Its private URL is `https://notes.l3b.cc.cd`. Caddy uses the existing wildcard certificate and private LAN/Tailscale policy, without a second proxy or Tinyauth login layer. Backend port `10.1.1.4:3010` maps to container port 3000; it is not published on all interfaces or exposed by a public Caddy handler.

## Runtime and persistence

`compose.yaml` is the sanitized source of truth. The official image is pinned by stable version and digest; Watchtower updates are disabled. Container name is `anchor`, restart policy is `unless-stopped`, memory cap is 768 MiB and CPU cap is one core. It uses its own `anchor_default` network, never `docknet`. The image bundles PostgreSQL 18, NestJS and Next.js in one container. There is no separate PostgreSQL/Redis service.

All state is bind-mounted from `/data/apps/anchor` to `/data`, including `/data/postgres` and uploaded assets. This is ctr's local data disk, not AV. Create the parent as root:70 mode 0750 so the bundled PostgreSQL user (UID/GID 70) can traverse it. The entrypoint creates the PostgreSQL subtree as 70:70 mode 0700. An initial root:root 0750 parent caused PostgreSQL startup to fail; correcting only the parent group fixed it. Do not recursively assign the entire tree to ctr or UID 1000. The official entrypoint needs root to initialize/chown PostgreSQL and run supervisor; it cannot simply be forced to `user: 1000:1000`. No privileged mode, host network or Docker socket is used, and `no-new-privileges` is enabled. The embedded database listens only on container loopback.

## Identity and secrets

The canonical HomeLab 1Password item is `Anchor`, with the exact URL `https://notes.l3b.cc.cd` and owner email `iam.anuragvishwakarma@gmail.com`. It contains the recovery password, `jwt-secret`, `database-password`, and `oidc-client-secret`. Portainer stack environment contains `JWT_SECRET`, `PG_PASSWORD`, and `OIDC_CLIENT_SECRET`; no secret value belongs in Git, Notion, or Homepage. The item was created once, not duplicated. Never reset the DB password only in Compose after the database is initialized: PostgreSQL's initialization password does not update existing roles.

Pocket ID client `anchor` is confidential with PKCE and restricted to `infrastructure-admins`. Issuer is `https://auth.l3b.cc.cd`, callback is `https://notes.l3b.cc.cd/api/auth/oidc/callback`, and launch/logout URL is `https://notes.l3b.cc.cd`. `DISABLE_INTERNAL_AUTH=false` preserves a local recovery login. Anchor links the existing account by its matching email during OIDC sign-in rather than creating a second owner.

Bootstrap used a temporary Portainer Stackfile with loopback-only `127.0.0.1:3010` and signup enabled. The first owner was registered through the native API and verified active/admin. The stack was then updated to the permanent tracked Compose with signup disabled and the private LAN bind before Caddy was enabled. On a completely fresh restore, repeat this bootstrap; the permanent `USER_SIGNUP=disabled` prevents creating the first password account. Pocket ID group restrictions are also important: v0.17.2's OIDC user-creation path does not visibly enforce the native signup setting, despite the README's general signup description. Do not rely on disabled native signup alone as OIDC authorization.

## Verification and operation

Verified on 2026-09-30: versioned health endpoint returns HTTP 200, native password login succeeds as admin, unauthenticated `/api/notes` returns 401, registration mode is disabled, and the real browser renders the authenticated notes dashboard without page errors. A generated note was created, edited and searched; an image was uploaded. After a Portainer API container restart, the note was readable and the attachment was byte-identical. Only that generated note and attachment were permanently removed afterward. The official icon `/icons/anchor_icon.png` returns HTTP 200. Idle container memory was about 164 MiB under the 768 MiB cap; this is a sample, not a guarantee for import peaks.

The Pocket ID authorization redirect uses client `anchor`, the exact HTTPS callback and S256 PKCE. See the dated main Notion update for the final browser OIDC check. No synthetic authorization tokens or passkey bypass were used.

Manage redeployment/restarts through Portainer, not a second Compose project. Check:

```sh
curl -fsS https://notes.l3b.cc.cd/api/health
curl -fsS https://notes.l3b.cc.cd/api/auth/registration-mode
ssh ctr 'sudo docker inspect anchor --format "{{.State.Health.Status}} {{.State.OOMKilled}}"'
```

For application exports, use Settings → Export & Import → Anchor backup ZIP. Preserve the full `/data` tree and vault secrets for complete disaster recovery. For a filesystem-level copy, stop Anchor through Portainer before copying its embedded PostgreSQL data, then restart and verify health/login. The existing whole-ctr backup includes its local data disk, but a new post-deployment backup restore has not been tested here. Do not claim replication is backup.

Upgrades: read release notes, obtain a consistent backup, select a stable version/digest, update the Portainer stack and tracked Compose together, verify health, native/OIDC login, note/attachment access and the Homepage card, then document and push. Do not downgrade across PostgreSQL migrations without restoring a compatible backup. Do not use the beta `next` tag.

Sources: [official release README](https://github.com/ZhFahim/anchor/blob/v0.17.2/README.md), [entrypoint](https://github.com/ZhFahim/anchor/blob/v0.17.2/docker/docker-entrypoint.sh), [OIDC account linking](https://github.com/ZhFahim/anchor/blob/v0.17.2/server/src/auth/oidc/oidc-user.service.ts).
