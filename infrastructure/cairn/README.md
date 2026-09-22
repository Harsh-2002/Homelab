# Cairn

Cairn is a single-node S3-compatible object store running as Portainer stack `cairn` on `ctr`. It is separate from the primary RustFS deployment and currently retains the recovered Cairn data set.

## Endpoints

| Purpose | URL | Exposure |
| --- | --- | --- |
| Management console | `https://cairn.l3b.cc.cd` | LAN/Tailscale only |
| S3 API | `https://cairn-s3.l3b.cc.cd` | LAN/Tailscale only |
| Health | `http://10.1.1.4:7373/healthz` | LAN |
| Readiness | `http://10.1.1.4:7373/readyz` | LAN |

The container publishes API port `7373` and console port `7374` from `ctr`. Caddy terminates TLS and enforces the private network boundary.

## Persistent state

The recovered state lives at `/data/apps/cairn` on `ctr` and is mounted at `/data` in the container. The directory contains both object bytes and `cairn.db`; keep them on the same filesystem so Cairn can use atomic rename correctly.

The Portainer stack preserves these sensitive values outside Git:

- `CAIRN_ROOT_ACCESS_KEY`
- `CAIRN_ROOT_SECRET_KEY`
- `CAIRN_MASTER_KEY`

Never rotate or lose `CAIRN_MASTER_KEY` without following Cairn's documented migration procedure. Existing sealed secrets depend on it.

## Operations

```bash
ssh ctr 'curl -fsS http://127.0.0.1:7373/healthz'
ssh ctr 'curl -fsS http://127.0.0.1:7373/readyz'
ssh ctr 'sudo docker logs --tail 100 cairn'
```

Source reference: [Cairn architecture and engineering specification](https://github.com/Harsh-2002/Cairn/blob/main/docs/overview.md).
