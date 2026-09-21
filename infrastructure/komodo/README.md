# Komodo archive

Komodo was evaluated as a Docker/Compose management plane for VM 204 `ctr`, while Argo CD and Headlamp remained the Kubernetes deployment and operations tools.

It was retired on 2026-09-21 by operator choice. No Komodo containers, data, proxy route, DNS/OIDC client, dashboard integration, or active credential remain. The former deployment manifests and credential records were intentionally removed; this file is retained only as an architectural decision record.

If Komodo is reconsidered, treat it as a fresh deployment: re-evaluate the current release and security posture, create new credentials and a new OIDC client, then add a new private Caddy route only after the service is operating.
