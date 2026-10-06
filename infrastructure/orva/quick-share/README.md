# Quick Share

Live function: `quick-share`, ID `01a110c1-cc79-7292-997d-11ac2d58d81e`.

URL: https://orva.l3b.cc.cd/fn/01a110c1-cc79-7292-997d-11ac2d58d81e

## Flow and expiry

The existing sandboxed Orva page uploads base64 JSON to its own function URL. The function decodes and validates the file, writes it into private Cairn bucket `artifact` under `quick-share/`, and returns a short link:

`https://orva.l3b.cc.cd/fn/01a110c1-cc79-7292-997d-11ac2d58d81e/s/<id>`

The ID is a random 128-bit, 22-character URL-safe token. Orva's native function subpath routing delivers `/s/<id>` to the same handler. The handler resolves its persistent manifest, checks expiry, and streams authenticated S3 GetObject bytes to the recipient. There is no redirect, signed S3 URL, new hostname, custom route, or separate shortening service. Cairn's endpoint and credentials are not included in the shared URL or response headers. This hides the backend from this sharing flow, not from the rest of the existing Cairn deployment. Orva's CSP sandbox remains unchanged.

Responses use `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and `X-Content-Type-Options: nosniff`. Raster images display inline; documents and SVG use attachment disposition with an encoded filename. Downloads consume Orva bandwidth and its existing concurrency/rate/timeout budgets. This is a small-file sharing proxy, not a large-file or video range-streaming service.

The UI offers 1 hour (default), 6 hours, 1 day, 3 days, and 7 days. The API accepts integer seconds from 60 through 604800, permitting a short end-to-end expiry test. Expiry above seven days is rejected. Links are bearer capabilities: anyone holding one may read the object until expiry. Avoid logging or committing them. Expiry cannot revoke copies already downloaded.

File limit is **4 MiB**, not 5 MiB: the current Orva request cap is 6 MiB and base64 adds about one third plus JSON overhead. This intentionally stays below the platform cap rather than introducing chunking or changing global request limits. Both UI and API enforce it. MIME allowlist covers images/documents; it is not malware or magic-byte scanning.

## Persistence and cleanup

Orva's bundled KV stores `share:<random-id>` with object key and absolute expiry. Records are persistent, not TTL-expired: cleanup must not lose its deletion manifest. The record is written before PUT so a failed upload remains eligible for idempotent cleanup. No blob is stored in KV and no separate database/service is added.

Schedule `01a110e2-c10d-78b3-b3de-f7ef27fc806b` runs `quick-share` with payload `{"action":"cleanup"}` every five minutes (`*/5 * * * *`). Only the platform-stamped `x-orva-trigger=cron` path may enter cleanup; external spoofed headers were tested and rejected with 403. Cleanup removes expired objects through S3 DeleteObject and deletes their KV records only after successful storage deletion. Failed deletes retain their manifest for retry. The proxy rejects expired links immediately with 410 before reading storage; removed or unknown manifests return 404. Physical deletion occurs on the next successful cleanup run, normally within five minutes, later if the platform/storage is unavailable or overloaded.

Cairn user `quick-share` (`5575ec76041b4257911984b5885e5b30`) has only PutObject, GetObject, and DeleteObject on `arn:aws:s3:::artifact/quick-share/*`. It has no bucket administration or anonymous-read grant. The artifact bucket is unversioned, so DeleteObject removes the object rather than creating only a versioned delete marker. Existing `S3_ACCESS_KEY` and `S3_SECRET_KEY` remain encrypted Orva secrets. No credential value is in this directory.

Runtime: Node, 0.5 CPU, 256 MiB memory, 30-second timeout, max concurrency 1, existing 10 requests/minute rate limit, egress enabled. Plain environment: Cairn endpoint, artifact bucket, us-east-1 region, path style, MAX_UPLOAD_BYTES=4194304. Network access uses the documented Proxmox Caddy HTTPS exception; direct LAN backend access remains blocked.

## Root cause and verification

The old browser PUT used Origin null because Orva intentionally serves function HTML in an opaque CSP sandbox. Cairn CORS allowed the ordinary Orva hostname, not null, and denied preflight with 403. Its credential also originally permitted PutObject only: uploads could succeed but signed GET and cleanup could not. Both issues were corrected without weakening CSP/CORS or making the bucket public.

On 2026-10-06, browser upload through the actual page succeeded and the returned PNG decoded at its original dimensions. Default signed expiry was 3600 seconds; the seven-day selector produced 604800 seconds and its image downloaded. A 4 MiB payload uploaded and downloaded byte-for-byte. Expiry over seven days returned 400 and spoofed HTTP cleanup returned 403. Short-lived test objects were used to validate expiration and scheduled deletion. For rollback, inspect deployment history and select original code hash `1a948f7b36b2681c94184f5f0f726768686d1142b5637d118fb04a6c9f4297af`; revert associated environment/settings and policy deliberately rather than assuming a code rollback restores them.

Source of truth is the live function plus tracked `handler.js` and `package.json`. Deploy using Orva's CLI/MCP deployment API, not a second host service. Only `@aws-sdk/client-s3` is required; the presigner dependency was removed. Current AWS SDK GetObject streaming documentation, `orva docs --raw`, and local Orva/Cairn source were consulted.

The real scheduler ran successfully and removed the short-expiry test manifests. Read-only Cairn metadata inspection confirmed the expired 4 MiB test object had no remaining object-version row. Remaining agent-created image tests and the earlier diagnostic text were explicitly deleted; no user objects were targeted. A signed link to the expired boundary object no longer decoded. Cleanup was temporarily run every minute for verification, then restored to every five minutes. Desktop and 390px mobile checks had no horizontal overflow. Local validation/cleanup regression tests pass: `node --test infrastructure/orva/quick-share/handler.test.js` (six tests). Follow-up design-hook triage replaced width animation with scaleX transforms. The inherited Inter font is intentionally preserved with a file-scoped value exception in `.impeccable/config.json`; the detector now reports no findings.

### Short-link proxy upgrade, 2026-10-06

Deployment `01a110f1-cc2a-7584-bf6b-cd8108fcbf96`, code hash `44494c4f7fc811d93b283046d0f68f0aeea88f620f184b0e91eddc6e772655fd`, replaces direct signed downloads. A browser-created PNG uploaded through the real page and decoded through its short link at the original 80×60 dimensions. Downloaded bytes matched, the response stayed on Orva without redirecting, and the link was 87 characters long. Nine local regression tests cover upload validation, cleanup retries/authorization, byte streaming, missing links, and expiry before storage access. Desktop and 390px mobile screenshots were inspected; no horizontal overflow. UI polish preserves the simple single-file flow, adds accessible status/error labels, expiry controls and a copy action, and respects reduced motion. No unrelated design changes or broad detector suppressions were added.

A live 4 MiB text upload and proxy download matched byte-for-byte, returned 200 without a Location header or redirect, and used no-store caching. After its 60-second test expiry, the same short link returned 410 while the object still existed, verifying expiry does not depend on cron timing. Both agent-created proxy test objects and their manifests were then explicitly removed. The other existing upload was preserved.
