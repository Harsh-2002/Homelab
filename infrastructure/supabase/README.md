# Supabase

The single active Supabase instance runs on Kubernetes, managed through Argo CD
application **supabase**. VM108, PocketBase, VM HA/replication/backup jobs and the
two VM backup archives were removed on 2026-10-18 at the owner's request.

## Access

| Interface | Endpoint |
| --- | --- |
| Studio | https://supabase.l3b.cc.cd |
| APIs | https://sb.l3b.cc.cd |
| MCP | https://sb.l3b.cc.cd/mcp |
| PostgreSQL session pooler | sb.l3b.cc.cd:5432 |

All access remains private to LAN/Tailscale through existing Caddy. Studio uses
Pocket ID/Tinyauth; Caddy injects the protected backend credential after SSO.
Applications use publishable/secret keys and user JWTs. MCP uses a separate
administrative Bearer key, not browser OAuth. `/api/mcp` is explicitly denied.
PostgreSQL requires TLS, e.g. `sslmode=verify-full`, with system CA trust.
The administrative pooler username is `postgres.homelab-production`, database
`postgres`. This is not a frontend credential. The tenant suffix is an existing
internal ID, not a second environment.

**One deployment is one Supabase project.** Apps can use separate schemas, grants,
RLS policies and buckets, but Auth, keys and lifecycle are shared. A service-role
key bypasses RLS. Independent projects require separate deployments.

Credentials live in **HomeLab → Supabase**, concealed `deployment-secrets` plus
labelled API/MCP/database fields. Existing Codex/Claude/Hermes MCP URLs and their
dedicated Bearer key were preserved. Never print vault contents, Kubernetes
Secret data, rendered runtime environments or client Authorization headers.

## Architecture and persistence

- CloudNativePG 1.30.1, two operator replicas. PostgreSQL 17.6, official
  `supabase/postgres:17.6.1.136`, one primary and two standbys across three nodes.
- Synchronous quorum requires one standby acknowledgement. Writes can stop when
  no eligible synchronous standby remains; do not silently weaken durability.
- Each database has its own 30Gi Longhorn RWO PVC, with the existing two-replica
  Longhorn policy. Logical replication slots are synchronized for Realtime.
- Auth, REST, Realtime, Kong, Meta, Studio, Edge Functions, Logflare and Supavisor
  each have two replicas. Supavisor uses IPv4 Erlang distribution, a shared
  protected cookie and pod-IP node names. Realtime uses headless DNS discovery.
- Storage is **one replica**, on `supabase-prod-storage-block`, 20Gi Longhorn RWO.
  One imgproxy replica is colocated and mounts the same filesystem. Kubernetes
  restarts these after failure; file service pauses during recovery. This is
  recovery HA, not active/active storage.
- Longhorn RWX uses NFS without the extended attributes required by Supabase's
  file backend. Do not switch Storage back to RWX or add Storage replicas against
  this RWO claim. The unsuccessful bootstrap RWX volume was deleted only after
  confirming no active workload used it.
- Functions and Studio snippets use separate 1Gi Longhorn RWX claims. Persistent
  JWT/crypto/pgsodium keys are restored from the canonical vault item, never
  regenerated against an existing database.
- Vector runs on every node in a separate privileged-policy logging namespace;
  its actual container drops capabilities and mounts logs read-only. It receives
  only Logflare's ingestion token, not database/admin credentials. Logflare uses
  PostgreSQL rather than BigQuery. Event retention is seven days via pg_cron.
- No new proxy, Redis, MinIO or external object store was deployed. No Longhorn
  backup target was added. Replicas are **not backups**; there is currently no
  independent backup/PITR protection for this instance by owner choice.

### Existing internal identifiers

The namespace remains `supabase-prod`, and some existing Kubernetes resource IDs
and the Helm release name retain `supabase-prod`. They are storage-bound legacy
identifiers, not an additional deployment. Public/service/Studio/Homepage/Argo CD
names are **Supabase**. Namespace/PVC identity changes require a planned data
migration and must not be implemented by deleting/recreating the live database.

### Gateway RCA

Cilium's default cross-node external service routing source-NATed Caddy requests
to a node's Cilium address. The Caddy-only ingress policy then rejected some
requests. Confirmed by Cilium policy-drop events showing a rewritten source.
The service now uses NodePort with `externalTrafficPolicy: Local`. Caddy health
checks all three nodes and selects those with local healthy pods. HTTP port32080
and PostgreSQL session port32432 accept only Caddy's source10.1.1.3. The internal
transaction pooler NodePort32643 is reserved, not exposed as a Caddy listener.
No cluster-wide Cilium mode was changed and no source allowlist was broadened.

## Reproduce and operate

### Database initialization contract and webhook RCA (2026-10-18)

#### Query Performance follow-up

The first repair's tests missed Studio Query Performance. Live inspection then
found `pg_stat_statements` preloaded but absent as a SQL extension in `postgres`.
The image's `00-extension.sql` includes its creation and the original bootstrap
logged that file, so historical evidence does not establish exactly when/why the
extension became absent. Do not claim it was certainly skipped or blame DNS.
The confirmed deployment defect was missing functional dependency validation.

GitOps job `supabase-observability-init-v4` now creates the extension in
`extensions`, checks preload and calls its statistics view. No database restart,
reset of statistics, broad grants, or application-data changes are required.
The acceptance script checks the full required platform extension inventory,
callable statistics on every database instance, and Studio's query/role/metrics/
cache-hit-rate SQL routes. A browser test verified the real Query Performance
page shows rows and metrics, no missing-extension/relation error, and HTTP200
for the data requests. Optional extensions remain optional. Fresh deployments
must complete v3 then v4 and pass these tests, not merely become pod-ready.

The initial CNPG bootstrap enumerated SQL files bundled in the database image,
but did not run the official Docker overlay files `98-webhooks.sql`,
`99-roles.sql`, and `99-jwt.sql`. Role passwords were reconciled separately,
but webhook objects and database JWT settings remained absent. This exposed
Studio's Enable button, which calls a platform `hook-enable` endpoint not
implemented by the deployed self-hosted Studio image. A direct request inside
Studio returned the same 404, ruling out Caddy/DNS as the cause.

`supabase-platform-init-v3` now runs the missing official overlays after the
original bootstrap. It uses a session advisory lock, conditional webhook schema
creation, explicit object validation and a versioned migration ledger. It can be
rerun without dropping application data. Argo CD manages this job for existing
and fresh deployments; do not edit/recreate the completed immutable v1 Job.
Future migrations get a new version/job, not an empty database or a replay of
all image initialization scripts. Preserve the original secrets.

`check-init-contract.py` checks every reviewed upstream overlay is present and
executed. Both secret bootstrap and component rendering invoke it. Supplying the
pinned upstream checkout additionally checks its declared overlay inventory, so
new upstream requirements must be reviewed instead of silently skipped.

Validation: `python3 infrastructure/supabase/validate-platform-init.py` verifies
the initialized objects/settings, exercises Studio's real extension list/query
routes with transactional hstore enable/disable, and inserts into a disposable
table with a real webhook trigger. An ephemeral in-memory HTTP receiver verifies
the POST payload and pg_net HTTP 200 result. It removes only its own fixtures.
No database or service restart is required for this repair.

This is not a reason to enable every optional extension. Extensions already
packaged by the image can normally be enabled through Studio/SQL with appropriate
privileges. New extension binaries or preload requirements need a reviewed image
and rolling database configuration change across all three instances. Some
hosted-only platform features are not implemented by self-hosted Studio.

Desired manifests: `gitops/apps/supabase`; app-of-apps entry:
`gitops/clusters/platform/applications/supabase.yaml`. Public component manifests
are generated from community chart source commit
`14806daa859670133b1139faebb473855806899a`, chart0.8.0, plus tracked compatibility
patches. The published0.8.0 package differs from that reviewed source; do not
silently substitute it. Components use the chart's pinned stable version tags.

1. Restore the canonical HomeLab Supabase vault item before provisioning.
2. Run `python3 infrastructure/supabase/bootstrap.py` from dev. This reuses keys
   and refuses to generate fresh keys if database PVCs already exist.
3. Sync the CloudNativePG operator Argo application, then the Supabase application.
   The bootstrap job waits for PostgreSQL, runs bundled Supabase migrations and
   records `homelab_bootstrap.state=v1`. It refuses a partial existing database.
4. Supabase image migrations clear service passwords, so the tracked final SQL
   reconciles them after migrations. CNPG requires its management `postgres`
   role to remain SUPERUSER; only the image's demotion statement is filtered.
5. Keep the pgsodium/Vault key helper configured for both extensions. Image
   UID/GID100:101, not CNPG's default user26. Realtime release commands run as
   nobody directly because its stock sudo entrypoint conflicts with dropped caps.
6. Sync Studio auth with `python3 infrastructure/supabase/sync-studio-auth.py`.
   Apply the tracked Caddy config with its protected env loaded, validate first,
   then reload. Tinyauth rules use the existing owner identity/admin group.
7. Run acceptance tools below. Do not mark deployment complete from TCP probes
   or Argo health alone. Check database quorum, actual APIs and persisted data.

To regenerate component YAML, clone the reviewed upstream commit, run
`python3 infrastructure/supabase/render-components.py /path/to/upstream`, review
the public output and update `gitops/apps/supabase/files/components.yaml` through
the normal Git workflow. The generator refuses Secret objects. Config checksums
roll Kong/Functions when their configuration changes. Preserve upstream Kong Lua
quoting; its entrypoint shell-expands the file before parsing YAML.

```sh
kubectl --context k8s -n supabase-prod get cluster,pods,pvc
kubectl --context k8s -n argocd get applications supabase cloudnative-pg
python3 infrastructure/supabase/validate-mcp.py
/home/dev/.local/share/homelab-tools/venv/bin/python infrastructure/supabase/validate.py
/home/dev/.local/share/homelab-tools/venv/bin/python infrastructure/supabase/validate-postgres.py
```

The acceptance venv requires `websocket-client==1.8.0` and
`psycopg[binary]==3.2.10`. Test fixtures are under the protected user state path
`~/.local/state/homelab/supabase-prod-acceptance.json`; `--keep` retains fixtures,
`--cleanup` removes only those fixtures. `validate-postgres.py --failover`
deliberately deletes the current primary pod, so use only in an approved window.

## SMTP

Sender **Anurag Vishwakarma (l3b)**, `l3bctl@gmail.com`, smtp.gmail.com:587 STARTTLS.
The canonical source is **HomeLab → Google → smtp**, a concealed Google app
password. `configure-smtp.py` validates login and updates the protected Supabase
vault record/Kubernetes Secret without printing it. Restart/roll Auth after
changing an existing Secret because process environment is not hot-reloaded.
Public signup remains disabled and email auto-confirm remains off.

SMTP authentication and submission to the homelab mailbox passed. A real
Supabase Auth invitation also returned success through Gmail; its disposable
Auth user was removed afterward. Inbox receipt was not independently observed.

## Verified 2026-10-18 and limits

- Studio SSO redirect/no Basic-auth prompt; spoofed identity and Basic bypass
  denied. Owner's passkey-authenticated Studio browser session still needs their
  confirmation; it was not bypassed or impersonated for testing.
- ES256 Auth and refresh, REST CRUD/two-user RLS isolation, private Storage and
  signed URL expiry, authenticated Edge Function, Realtime WebSocket changes/RLS.
- Database rows and private file survived Storage pod recreation and database
  primary failover. One acknowledged SQL marker survived automatic promotion
  from supabase-db-1 to supabase-db-2. SQL recovery measured123.6s for normal pod
  termination with graceful shutdown. This is not a zero-downtime guarantee or a
  full node/network-partition/fencing drill. Three DB instances returned healthy.
- TLS PostgreSQL access through sb:5432 and Supavisor SQL writes passed. Supavisor
  replica clustering was checked through its runtime node list.
- MCP auth, discovery and real database queries/writes tested independently.
- Node-local gateway routing preserves Caddy's source identity. Direct requests
  from dev to the raw backend must remain denied.
- Kubernetes1.37 is listed as tested, not formally supported by CNPG1.30.1; owner
  explicitly accepted this limitation. Supported upstream range is1.34–1.36.
- Full disaster recovery, independent backups, sustained load/capacity and whole
  node failure remain untested. No blanket production-readiness claim is made.

Sources: [Supabase self-hosting](https://supabase.com/docs/guides/self-hosting),
[community Kubernetes chart](https://github.com/supabase-community/supabase-kubernetes),
[CloudNativePG](https://cloudnative-pg.io/docs/1.30/),
[Cilium source preservation](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/).
