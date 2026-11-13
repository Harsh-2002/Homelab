# Upstream

- Repository: https://github.com/cloudflare/security-audit-skill
- Path: `skills/security-audit`
- Commit: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8` (2026-09-14)
- License: MIT (see `LICENSE`)

Vendored without changes to the upstream audit content except for the local `OPENCODE.md` adapter and a pointer to it in `SKILL.md`. The upstream validators and tests are included unchanged; run them with:

```sh
node validate-findings.test.cjs
node validate-coverage-ledger.test.cjs
```
