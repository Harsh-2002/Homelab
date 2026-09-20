# Komodo

Komodo v2.3.3 manages Docker and Compose workloads on VM 204 `ctr`. It does not manage Kubernetes; Argo CD remains the Kubernetes deployment controller, and Headlamp is the recommended Kubernetes operations UI.

MongoDB 8 requires AVX. VM 204 is configured for Proxmox CPU type `host`; both permitted HA nodes have matching Intel Core i5-8400T processors with AVX and AVX2. This CPU change is pending the next safe VM reboot because the recovery extraction is active. The Komodo containers are created but intentionally stopped until that reboot.

## Deployment

The tracked Compose file is installed at `/data/apps/komodo/compose.yaml`. The live `compose.env` is mode `0600`, generated locally on `ctr`, and must never be committed.

```bash
cd /data/apps/komodo
docker compose --env-file compose.env config --quiet
docker compose --env-file compose.env pull
docker compose --env-file compose.env up -d
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
docker compose --project-directory /data/apps/komodo --env-file /data/apps/komodo/compose.env ps
curl --fail --silent --show-error http://10.1.1.4:9120/
```

Retrieve the initial username without printing secrets:

```bash
sudo sed -n 's/^KOMODO_INIT_ADMIN_USERNAME=//p' /data/apps/komodo/compose.env
```

Retrieve the one-time password only when ready to log in:

```bash
sudo sed -n 's/^KOMODO_INIT_ADMIN_PASSWORD=//p' /data/apps/komodo/compose.env
```

After changing the administrator password in Komodo, remove the two `KOMODO_INIT_ADMIN_*` lines from the live environment file and redeploy Core. Database backups under `/data/apps/komodo/backups` are replicated with VM 204 but are not an independent backup.
