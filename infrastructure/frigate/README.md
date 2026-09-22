# Frigate

Frigate runs as Portainer stack `frigate` on the `ctr` Docker VM, using the Intel iGPU's `/dev/dri/renderD128` device for VAAPI decoding. It is deliberately not privileged: only the device, its host `video` and `render` groups, and the narrow `PERFMON` capability required for Intel GPU telemetry are passed explicitly. The VM applies `kernel.perf_event_paranoid=2` so that capability can access the performance event system. The container uses Intel's supported modern `iHD` VAAPI driver automatically; no legacy driver override is set. VAAPI decoding and GPU scaling are verified from the live FFmpeg process. The authenticated UI is bound only to `10.1.1.4:8971` and served privately at `https://frigate.l3b.cc.cd` by Caddy.

## Identity

Frigate does not implement OIDC itself. Pocket ID is supplied through Tinyauth and Caddy's `forward_auth` flow. Caddy forwards the authenticated `Remote-User` and `Remote-Groups` headers, plus a separate proxy secret. Frigate therefore disables its unrelated local login and maps `infrastructure-admins` to the Frigate `admin` role. The proxy secret is shared only by Caddy and this Stack runtime environment; it is stored in the existing `HomeLab` 1Password item **Frigate**, never in Git.

## Storage and retention

The durable application paths are `/data/apps/frigate/config` and `/data/apps/frigate/media`. Recovery restores configuration, Frigate's database, model cache, and operational metadata. Historic recordings, clips, and exports from `/EX` are intentionally not restored.

Frigate starts with an empty media directory. It keeps motion recordings, alert recordings, detection recordings, and snapshots for at most seven days. Continuous recording is disabled. A Frigate cleanup pass removes expired media automatically.

## Operations

Portainer supplies real runtime values; the tracked template is intentionally non-secret. Validate after a restart:

```bash
sudo docker compose -f /data/apps/frigate/compose.yaml ps
sudo docker logs --tail 100 frigate
curl --resolve frigate.l3b.cc.cd:443:10.1.1.3 -I https://frigate.l3b.cc.cd
```

The record path uses `-c:v copy`: recordings retain the source video rather than being unnecessarily transcoded. The detect path uses `preset-vaapi`, which decodes and scales frames on the Intel GPU. Confirm the Frigate system page reports VAAPI hardware acceleration and that access redirects through Pocket ID when no Tinyauth session exists.
