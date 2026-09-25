# n8n

Portainer Stack 85 `n8n` on `ctr` owns the entire n8n application group: n8n, PostgreSQL, the SearXNG web-search backend, and the three-service n8n Sandbox deployment. The former separate sandbox Stack 150 was deleted after consolidation. The tracked Compose file is the sanitized source of truth; Portainer Stack environment values supply secrets.

## Internal endpoints

| Consumer | Endpoint |
| --- | --- |
| Browser through Caddy | `https://n8n.l3b.cc.cd` |
| n8n to SearXNG | `http://searxng:8080` |
| n8n to Sandbox API | `http://sandbox-api:8080` |

SearXNG and both long-running sandbox services publish no host ports. Their visible Docker container names are `searxng`, `sandbox-api`, `sandbox-runner`, and the one-shot `sandbox-certs`; numeric Compose suffixes are not used. The runner's internal Compose service name remains `sandbox-runner-1` because that identity is part of the official mTLS certificate layout. SearXNG serves JSON because `searxng-settings.yml` adds `json` to its response formats, as required by n8n Assistant. The sandbox runner remains isolated on `sandbox-control`; only the API also joins the default stack network.

The Portainer Stack environment contains `N8N_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `N8N_SANDBOX_VERSION`, the three sandbox secrets, and `SEARXNG_SECRET`. The encryption key, database password, and SearXNG secret are concealed fields in the existing `HomeLab` item `N8N`; the sandbox keys remain in the existing item `n8n Sandbox`. Never commit their values.

The stack currently runs n8n `2.40.7`, SearXNG `2026.9.25-487f51922`, and Sandbox Service `1.4.0`. The SearXNG Compose image follows the official `latest` tag; review release changes before intentionally redeploying a newer digest.

The sandbox runner admits at most four concurrent sandboxes. Each defaults to 512 MB RAM, one CPU, and 256 processes. Idle sandboxes stop after 30 minutes and are deleted after 24 hours. The API persists its SQLite state at `/data/apps/n8n-sandbox/api`, and the retained external `n8n-sandbox_sandbox-tls` volume contains its mTLS material. Per-sandbox disk quota is not enabled because the nested Docker quota pool needs a loop device that `ctr` does not expose.

## Validation

```bash
ssh ctr 'sudo docker exec n8n wget -qO- http://sandbox-api:8080/healthz'
ssh ctr 'sudo docker exec n8n wget -qO- "http://searxng:8080/search?q=n8n&format=json"'
ssh ctr 'sudo docker ps --filter label=com.docker.compose.project=n8n'
```

The first command must return `{"status":"ok"}`. The search response must be valid JSON with a `results` array. After consolidation, a vault-authenticated test created an ephemeral no-egress sandbox, executed `printf sandbox-ok`, received a successful exit event, and deleted the sandbox with HTTP 204. This validates n8n-network DNS, API authentication, mTLS, the runner, and nested execution.

References: [n8n Assistant web search](https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-n8n-assistant/#enable-web-search) and [official Compose guide](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose/).
