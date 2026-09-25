# n8n code sandbox

The n8n Sandbox Service runs on `ctr` as the Portainer-managed `n8n-sandbox` stack. It provides isolated code execution for n8n Assistant and Agents.

## Topology

| Service | Purpose | Exposure |
| --- | --- | --- |
| `sandbox-certs` | One-time mTLS certificate bootstrap | None; exits successfully |
| `sandbox-api` | API used by n8n | `http://sandbox.internal:8080` on `n8n_default` only |
| `sandbox-runner-1` | Privileged Docker-in-Docker execution runner | Sandbox control network only |

The stack is pinned to Sandbox Service `1.4.0`. The API and runner use mTLS on their control paths. No sandbox port is published on `ctr`, Caddy, LAN, or the internet. The API persists its SQLite state at `/data/apps/n8n-sandbox/api`; generated certificates use the Portainer stack volume.

The runner admits at most four concurrent sandboxes. Each sandbox defaults to 512 MB RAM, one CPU, and 256 processes. Idle sandboxes stop after 30 minutes and are deleted after 24 hours. The outer runner is limited to 3 GB RAM and two CPUs because `ctr` has four CPUs and 8 GB RAM. Per-sandbox disk quotas remain at the upstream default because the Docker-in-Docker quota pool requires a loop device that this VM does not expose.

## Credentials and n8n configuration

The HomeLab 1Password item `n8n Sandbox` contains the n8n-facing API key plus the internal registration and runner keys. Secrets are Portainer stack environment variables and are not stored in Git or Notion.

Enter these values in n8n's code-sandbox settings:

```text
Service URL: http://sandbox.internal:8080
API key: op://HomeLab/n8n Sandbox/credential
```

If configuring n8n through environment variables instead of its UI, use:

```text
N8N_INSTANCE_AI_SANDBOX_ENABLED=true
N8N_INSTANCE_AI_SANDBOX_PROVIDER=n8n-sandbox
N8N_SANDBOX_SERVICE_URL=http://sandbox.internal:8080
N8N_SANDBOX_SERVICE_API_KEY=<API key from 1Password>
```

The Assistant also needs `instance-ai` enabled and a supported model-provider key. Those are separate from the sandbox credential.

## Operations

```bash
ssh ctr 'sudo docker ps --filter label=com.docker.compose.project=n8n-sandbox'
ssh ctr 'sudo docker exec n8n wget -qO- http://sandbox.internal:8080/healthz'
ssh ctr 'sudo docker logs n8n-sandbox-sandbox-api-1 --tail 100'
ssh ctr 'sudo docker logs n8n-sandbox-sandbox-runner-1-1 --tail 100'
```

The health response must be `{"status":"ok"}`. Confirm the API log shows a registered runner before using the service. Upgrade all three sandbox images to the same stable service release; mixed versions are unsupported. Regenerating the `sandbox-tls` volume changes the mTLS trust material and requires recreating both the API and runner.

The deployed stack was validated from inside the `n8n` container with the vault-backed API key: it created an ephemeral no-egress sandbox, executed `printf sandbox-ok`, received a successful exit event, and deleted the test sandbox with HTTP 204. This proves the API authentication, n8n-network DNS, mTLS control channel, runner, and nested execution path rather than only the shallow health endpoint.

References: [n8n Assistant setup](https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-n8n-assistant/), [official Docker Compose guide](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose/), and [Sandbox Service releases](https://github.com/n8n-io/n8n-sandbox-service/releases).
