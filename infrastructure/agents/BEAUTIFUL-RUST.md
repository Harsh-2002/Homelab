# Beautiful Rust for all four agents

Installed on dev, 2026-10-26, from
[morganlinton/BeautifulRust](https://github.com/morganlinton/BeautifulRust),
revision `a2b22682fa69b5e2d41a5d041663df7d51aac521` (MIT).

## Installed skills

| Name | Use |
| --- | --- |
| rust-best-practices | Writing, changing, debugging and explaining Rust |
| rust-review | Prioritized code review with rule citations and concrete fixes |
| rust-port | Behavior-preserving ports to Rust, starting with the original tests |

The complete upstream folders, including reference digests and evaluation
fixtures, live under `~/.agents/skills/`. Each has its MIT LICENSE. Codex,
Claude Code and Hermes have same-name directory symlinks in `~/.codex/skills/`,
`~/.claude/skills/` and `~/.hermes/skills/`. OpenCode already reads the shared
root and resolves the same files. This keeps one local copy per skill.
No native memory plugin, MCP credential, model or permission setting changed.

All three were also installed through OpenViking's native skill installer at
`viking://agent/skills/rust-best-practices`, `rust-review`, and `rust-port`,
with their supporting files. Local skills take precedence; agents on another
machine can retrieve the shared account copies through native memory tools.
This is discoverable guidance, not a guarantee that every model follows it.

## Clippy reference assets

Upstream README, MIT LICENSE and complete `lints/` are retained under
`~/.local/share/beautiful-rust/a2b22682fa69b5e2d41a5d041663df7d51aac521/`.
No Cargo.toml, Rust project or CI lint settings were changed. Adopt the lints
per project after checking its MSRV and whether library-only rules fit. The
upstream suppression rules require Rust 1.81 or later.

## Reproduce on a new dev account

Review the pinned source first. With the standard Codex skill installer present:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo morganlinton/BeautifulRust \
  --ref a2b22682fa69b5e2d41a5d041663df7d51aac521 \
  --path skills/rust-best-practices skills/rust-review skills/rust-port \
  --dest ~/.agents/skills
```

The installer refuses existing destinations. From a checkout at that exact
revision, copy LICENSE into each installed skill. Link each skill by name into
the other three harness skill directories using ordinary `ln -s` without force;
stop and compare any existing entry. OpenCode's protected config must keep
`/home/dev/.agents/skills` in its skills roots. Copy README, LICENSE and lints
into the revision-specific reference-assets directory above. The tracked
`beautiful-rust.lock.json` contains all expected local file hashes.

For the shared account, first inspect existing names with OpenViking read.
Use native add_skill with the pinned Git source
`https://github.com/morganlinton/BeautifulRust/tree/a2b22682fa69b5e2d41a5d041663df7d51aac521/skills`,
the three selected names, and `target_uri=viking://agent/skills`. Do not
blindly replace newer shared skills. The Git installer supports a multi-skill
source; a local ZIP containing three top-level skill directories returned 500
and was not the successful installation path.

## Verification and updates

- Upstream check-skill.py: zero errors and warnings.
- Codex app-server skills/list: all three enabled.
- Claude Code native initialization: all three in slash_commands.
- Hermes skills list --source local --enabled-only: all three enabled.
- OpenCode native /api/skill: all three complete records discovered. Its CLI
  truncates very large responses; parse complete records without printing the
  entire skill catalog or treating truncated JSON as a server failure.
- OpenViking read: installed skill bodies and a bundled reference were readable.
- python3 infrastructure/agents/check-integrations.py: MCP parity and full
  file-hash parity for all three skills and the lint reference assets passed.

No Rust build or agent-quality evaluation was run: this task installed guidance
and reference assets, without changing a Rust application. Start a new agent
conversation if its current skill catalog is cached. No service restart is
required for this installation.

Updates are reviewed, not automatic: compare the new upstream revision, use
the installer into a staging directory, preserve local changes, replace the
canonical folders deliberately, update reference assets and lock hashes, then
reinstall the shared OpenViking copies and repeat discovery/integrity checks.
Do not install an additional Claude marketplace copy of these same skills
unless intentionally replacing the shared-directory approach.

## OpenViking authentication follow-up

The shared import initially failed because its Codex OAuth refresh returned401.
Ran the existing scripts/refresh-openviking-codex.sh to import the current dev
login without displaying or staging tokens. No container restart, VLM model,
embedding change or memory reset. The retry installed all three skills; doctor
passed VLM gpt-6-luna and local all-minilm embeddings. Its separate existing
VikingBot user-key configuration warning remains; no bot setting was changed.
