# Pulse evaluation archive

Pulse `v6.4.1` was evaluated on 2026-09-20 and then completely removed because its user interface was not a good fit. This file is historical guidance only: there is no active Pulse server, route, identity integration, agent, API credential, HA resource, replication job, or Kubernetes workload.

## Evaluated architecture

The evaluation used a native systemd server in an unprivileged Debian LXC with 2 vCPU, 2 GiB RAM, and a 25 GiB ZFS root disk. Caddy supplied private TLS access, Pocket ID supplied OIDC, Proxmox was queried with `PVEAuditor`, Kubernetes used a read-only DaemonSet, and the Docker host used a native agent with remote command execution disabled.

The deployment worked technically, including retained metrics, alerts, Proxmox HA, and five-minute ZFS replication. It was removed by operator choice rather than because of a reliability failure.

## If evaluating again

Treat a future deployment as new work rather than attempting to recover the removed instance:

1. Review the current Pulse release, license, security model, and documentation.
2. Pin an explicit version and verify the signed installer.
3. Create a new dedicated LXC and new IP; do not assume the former CT ID or address remains free.
4. Create new least-privilege Proxmox and agent credentials.
5. Create a new Pocket ID client and Caddy route.
6. Put Kubernetes configuration in Git, but keep tokens out of Git and Notion.
7. Validate the UI before investing in HA, retained history, and notification integrations.
8. Add HA and replication only after the product is accepted.

Never reuse secrets from the former evaluation. They were revoked and securely removed as part of the uninstall.
