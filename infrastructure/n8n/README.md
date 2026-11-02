# n8n

Portainer Stack 85 `n8n` on `ctr` owns the entire n8n application group: n8n, PostgreSQL, the SearXNG web-search backend, and the three-service n8n Sandbox deployment. The former separate sandbox Stack 150 was deleted after consolidation. The tracked Compose file is the sanitized source of truth; Portainer Stack environment values supply secrets.

## Internal endpoints

| Consumer | Endpoint |
| --- | --- |
| Browser through Caddy | `https://n8n.l3b.cc.cd` |
| n8n to SearXNG | `http://searxng:8080` |
| n8n to Sandbox API | `http://sandbox-api:8080` |
| Sandbox API to runner control | `sandbox-runner-1:9091` (mTLS, `sandbox-control` network) |

SearXNG and both long-running sandbox services publish no host ports. Their visible Docker container names are `searxng`, `sandbox-api`, `sandbox-runner`, and the one-shot `sandbox-certs`; numeric Compose suffixes are not used. The runner's internal Compose service name remains `sandbox-runner-1` because that identity is part of the official mTLS certificate layout. SearXNG serves JSON because `searxng-settings.yml` adds `json` to its response formats, as required by n8n Assistant. The sandbox runner remains isolated on the stack-local `sandbox-control` network; only the API also joins `l3b`.

The sandbox secrets live in protected root-owned files under `/data/apps/n8n-sandbox`: `api.env`, `runner.env`, and `n8n.env`. They are mode `0600`, sourced from the concealed fields of the existing `HomeLab` item `n8n Sandbox`, and expanded by `infrastructure/l3b/portainer-api.py` into the Stack environment on deploy. Never commit their values.

The stack currently runs n8n `2.45.7`, SearXNG `2026.11.1-10db664f1`, and Sandbox Service `1.4.0`. Sandbox image tags are pinned literally in the Compose file so the stack deploys without extra environment arguments; bump all three together after reviewing release notes. The SearXNG Compose image follows the official `latest` tag.

The sandbox runner admits at most four concurrent sandboxes. Each defaults to 512 MB RAM, one CPU, and 256 processes. Idle sandboxes stop after 30 minutes and are deleted after 24 hours. The API persists its SQLite state at `/data/apps/n8n-sandbox/api`, and the stack-managed `n8n_sandbox-tls` volume holds its mTLS material. The certificate bootstrap is idempotent and keeps existing PEMs. Per-sandbox disk quota is not enabled because the nested Docker quota pool needs a loop device that `ctr` does not expose.

## Validation

```bash
sudo docker exec n8n wget -qO- http://sandbox-api:8080/healthz
sudo docker exec n8n wget -qO- "http://searxng:8080/search?q=n8n&format=json"
sudo docker ps --filter label=com.docker.compose.project=n8n
sudo docker inspect sandbox-api sandbox-runner --format '{{.Name}} {{.State.Health.Status}}'
```

The first command must return `{"status":"ok"}`. The search response must be valid JSON with a `results` array. A vault-authenticated test creates an ephemeral sandbox, executes `printf sandbox-ok`, and deletes it with HTTP 204; the sandbox API logs `runner_healthy:true` on creation. This validates n8n-network DNS, API authentication, mTLS, the runner, and nested execution.

References: [n8n Assistant web search](https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-n8n-assistant/#enable-web-search) and [official Compose guide](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose/).
