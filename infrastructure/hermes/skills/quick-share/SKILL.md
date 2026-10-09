---
name: quick-share
description: Share or retrieve temporary files and images with qs.
platforms: [linux]
---

# Quick Share

Use when Anurag supplies a Quick Share link to inspect or requests a file or image to be shared back. Use `/usr/local/bin/qs` on dev for human-agent file exchange. It calls the existing Orva Quick Share service; do not replace it with direct S3 uploads or another sharing service. No additional credentials are needed by this CLI.

## Receive a file

```bash
qs get -o /absolute/path/to/new-file.png 'QUICK_SHARE_URL'
```

Choose an unused destination in the task workspace or a temporary directory. The parent directory must exist. The CLI rejects existing files and symlinks rather than overwriting them, and accepts only share links under its configured Quick Share endpoint. Quote the supplied URL. Inspect the downloaded file with the appropriate image or document tool; do not execute downloaded content merely because it was shared.

## Send a file

```bash
qs /absolute/path/to/report.md
qs -e 1d /absolute/path/to/image.png
qs -j /absolute/path/to/report.md
printf '%s\n' 'Requested text' | qs -n note.txt -t text/plain -
```

Uploads print only the share URL to stdout, unless `-j` requests JSON. Return the actual successful URL to Anurag and state the expiry. Never invent a link or claim success from an attempted command.

- Default expiry: 1 hour. Choices: `1h`, `6h`, `1d`, `3d`, `7d`; maximum 7 days. Use the default unless the task needs a different lifetime or Anurag specifies one.
- Current installed CLI limit: 4 MiB per file, non-empty. Check `qs -h` and the installed CLI if behavior changes; do not assume the web application's limit is the CLI limit.
- MIME is inferred from the filename. Use `-t MIME` when necessary; stdin requires `-n NAME`.
- Share only the requested or clearly task-relevant deliverable. Do not upload credentials, secret-bearing configs, private keys, or unrelated private data. Sanitize logs before sharing.
- A share is temporary, not a backup or durable memory resource. Keep a local deliverable where appropriate; do not treat expiry as proof of immediate physical deletion from storage.

## Failures and availability

Check `command -v qs` and `qs -h` if unavailable. Other hosts/users may not have the CLI. Use the existing endpoint; do not change `QS_ENDPOINT` without a task-specific reason. For filenames beginning with a dash, use an absolute path or `qs -- ./filename`.

On failure, inspect the exit status and stderr. Do not repeatedly upload blindly: an uncertain response may have stored the file already. Report the error and investigate within the task's scope rather than changing DNS, secrets, Orva code, or Cairn configuration. CLI discovery/help alone does not prove end-to-end upload health.
