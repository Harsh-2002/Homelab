# Frigate

Frigate runs as Portainer stack `frigate` on the `ctr` Docker VM, using the Intel iGPU's `/dev/dri/renderD128` device for VAAPI decoding and OpenVINO object detection. It is deliberately not privileged: only the device, its host `video` and `render` groups, and the narrow `PERFMON` capability required for Intel GPU telemetry are passed explicitly. The VM applies `kernel.perf_event_paranoid=2` so that capability can access the performance event system. The container pins Intel's `i965` VAAPI driver: it is stable with this camera pipeline, whereas the tested `iHD` path produced VAAPI frame-download errors. VAAPI decoding and GPU scaling remain enabled. OpenVINO uses Frigate's bundled SSD MobileNet model on the detected Intel `GPU` device instead of the test-only CPU detector. Frigate is pinned to `0.18.0`; the pre-upgrade live configuration and database were copied under `/data/apps/frigate/backups/2026-09-22-pre-0.18` before this version change. The authenticated UI is bound only to `10.1.1.4:8971` and served privately at `https://frigate.l3b.cc.cd` by Caddy.

## Identity

Frigate does not implement OIDC itself. Pocket ID is supplied through Tinyauth and Caddy's `forward_auth` flow. Tinyauth must approve every request before Caddy proxies it; Caddy then supplies the fixed identity and `infrastructure-admins` role for the sole allowlisted Frigate user, plus a separate proxy secret. This avoids the Frigate 0.17 proxy-header UI regression while preserving Pocket ID as the only browser login. Frigate disables its unrelated local login and maps that group to the Frigate `admin` role. The proxy secret is shared only by Caddy and this Stack runtime environment; it is stored in the existing `HomeLab` 1Password item **Frigate**, never in Git. It must be present in both the Portainer Stack environment and `/etc/caddy/cloudflare.env`; restart Caddy after changing the latter so systemd loads the value.

Caddy redirects Frigate's obsolete `/login` route to `/`. This prevents a browser left on the native-login page from repeatedly loading a form that cannot authenticate when proxy auth is enabled.

## Storage and retention

The durable application paths are `/data/apps/frigate/config` and `/data/apps/frigate/media`. Recovery restores configuration, Frigate's database, model cache, and operational metadata. Historic recordings, clips, and exports from `/EX` are intentionally not restored.

Frigate starts with an empty media directory. It keeps motion recordings, alert recordings, detection recordings, and snapshots for at most seven days. This is a rolling window: cleanup runs hourly and removes expired segments rather than creating weekly copies. Continuous recording is disabled. The main stream measured about 4.35 Mb/s, which would require roughly 306 GiB for seven continuous days and leave insufficient headroom on the shared 500 GB data disk for the other services. Motion/event retention preserves source-quality footage with five seconds of pre-capture and post-capture while keeping storage bounded.

The single `outdoor` camera records the full-resolution main stream and detects at 640×360 and 5 FPS from its substream. People are high-priority alerts and dogs are lower-priority detections. The changing timestamp overlay is motion-masked, and the named `courtyard` zone covers the walkable approach for filtering and automation metadata. The zone is intentionally not required for review items, so objects at the edge of the image are not silently discarded.

## Operations

Portainer supplies real runtime values; the tracked template is intentionally non-secret. Validate after a restart:

```bash
sudo docker compose -f /data/apps/frigate/compose.yaml ps
sudo docker logs --tail 100 frigate
curl --resolve frigate.l3b.cc.cd:443:10.1.1.3 -I https://frigate.l3b.cc.cd
```

The record path uses `-c:v copy`: recordings retain the source video rather than being unnecessarily transcoded. The detect path uses `preset-vaapi`, which decodes and scales frames on the Intel GPU. Confirm the Frigate system page reports VAAPI hardware acceleration and that access redirects through Pocket ID when no Tinyauth session exists.
