# Komodo

Komodo v2.3.3 manages Docker and Compose workloads on VM 204 `ctr`. It does not manage Kubernetes; Argo CD remains the Kubernetes deployment controller, and Headlamp is the recommended Kubernetes operations UI.

MongoDB 8 requires AVX. VM 204 is configured for Proxmox CPU type `host`; both permitted HA nodes have matching Intel Core i5-8400T processors with AVX and AVX2. A controlled HA stop/start activated this CPU model and four vCPUs after the recovery extraction completed. The fixed container names are `komodo-mongo`, `komodo-core`, and `komodo-periphery`.

## Deployment

The tracked Compose file is installed at `/data/apps/komodo/compose.yaml`. The live `compose.env` is owned by `root`, mode `0600`, generated locally on `ctr`, and must never be committed. Always pass it explicitly: Compose uses it both to interpolate volume paths and to populate the Core/Periphery environments.

```bash
cd /data/apps/komodo
sudo docker compose --env-file compose.env config --quiet
sudo docker compose --env-file compose.env pull
sudo docker compose --env-file compose.env up -d
```

Persistent state:

```plain text
/data/apps/komodo/mongo
/data/apps/komodo/mongo-config
/data/apps/komodo/keys
/data/apps/komodo/backups
/data/apps/komodo/workspace
```

Access is through `https://komodo.l3b.cc.cd`. Caddy applies the shared private-source policy before proxying to `10.1.1.4:9120`. Komodo authentication remains enabled as a second layer, and public user registration is disabled.

Validate:

```bash
sudo docker compose --project-directory /data/apps/komodo --env-file /data/apps/komodo/compose.env ps
curl --fail --silent --show-error http://10.1.1.4:9120/
```

The local break-glass administrator is `iam.anuragvishwakarma@gmail.com`. Its password is authoritative in the existing `HomeLab` 1Password item named `Komodo`; it was generated, rotated into the live local account, and verified with a fresh local-login request. Pocket ID OIDC is the normal access path. The one-time `KOMODO_INIT_ADMIN_*` values were removed from the live environment after the rotation so they cannot become stale copies of a credential.

Database backups under `/data/apps/komodo/backups` are replicated with VM 204 but are not an independent backup.

## OIDC first-login procedure

`KOMODO_DISABLE_USER_REGISTRATION=true` and `KOMODO_DISABLE_OIDC_USER_REGISTRATION=true` are the secure steady-state values. A Pocket ID client restriction is the outer gate, but Komodo also blocks creation of new local and OIDC users.

For the first Pocket ID sign-in after deployment, temporarily set `KOMODO_DISABLE_OIDC_USER_REGISTRATION=false` and `KOMODO_ENABLE_NEW_USERS=true`, recreate Core with the explicit environment file, and sign in once. Restore both secure values immediately afterward. Komodo creates subsequent OIDC accounts as enabled non-administrators; use the bootstrap local administrator to promote the verified OIDC account from **Settings → Users**. Do not leave OIDC registration enabled.

The initial deployment created the canonical OIDC account `iam-anuragvishwakarma`, then verified and promoted it to administrator and super-administrator. The bootstrap local account remains break-glass only.

## Homepage metrics identity

Komodo has a non-human `homepage` service user for the Homepage summary widget. It is enabled with read access to the `Server` and `Stack` resource types only. It has no execute, write, inspect, terminal, log, create-server, or create-build permission. Its API key and secret are stored as `Homepage` fields in the existing `HomeLab` 1Password item named `Komodo`; no credential is stored in Git or in `compose.env`.
