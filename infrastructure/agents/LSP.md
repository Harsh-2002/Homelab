# Language servers on dev

Status as of **2 November 2026**. Verified with `hermes lsp status` and live LSP
`initialize` handshakes against the installed servers.

## OpenCode does not run language servers

OpenCode **v2.2.5** accepts and preserves `lsp` in
`~/.config/opencode/opencode.json`, but it does not run language servers, expose
LSP tools, or produce LSP diagnostics. This is stated in the OpenCode V2
migration guide:

> V2 accepts and preserves `lsp` configuration, but it does not run language
> servers, expose LSP tools, or produce LSP diagnostics.

The `lsp` block was removed on 2 November 2026. Re-adding it has no effect beyond
schema acceptance, so do not use it expecting diagnostics.

## Hermes owns LSP

Hermes Agent **v0.22.5** runs real language servers as background subprocesses and
feeds their semantic diagnostics into the post-write lint check used by
`write_file` and `patch`. Servers start lazily and are torn down when idle;
`hermes lsp status` reports `active clients: none` outside an edit.

| Language | Server | Location | Extensions |
| --- | --- | --- | --- |
| Go | `gopls` v0.24.0 | `~/.hermes/lsp/bin` | `.go` |
| Python | `pyright` | `~/.hermes/lsp/bin` | `.py`, `.pyi` |
| TypeScript/JS | `typescript-language-server` + TypeScript 6.0.3 | `~/.hermes/lsp` | `.ts .tsx .js .jsx .mjs .cjs .mts .cts` |
| YAML | `yaml-language-server` | `~/.hermes/lsp/bin` | `.yaml`, `.yml` |
| Rust | `rust-analyzer` 0.3.3105 | `~/.local/bin` | `.rs` |
| Bash | `bash-language-server` 5.8.1 | `~/.local/bin` | `.sh .bash .zsh .ksh` |

`bash-language-server` additionally requires **shellcheck** (apt, 0.10.0). Without
it Bash diagnostics are empty rather than absent — the server runs but reports
nothing.

## TypeScript 7 must not back tsserver

The global `tsc` is TypeScript **7.0.2**, the Go-native port, which ships no
`lib/tsserver.js` or `lib/typescript.js`. `typescript-language-server` cannot use
it as its SDK and fails with `Could not find a valid TypeScript installation`.

Hermes therefore installs its own copy in `~/.hermes/lsp`:

- `bin/typescript-language-server`
- `node_modules/typescript` pinned to **6.0.3**

Do not upgrade the Hermes copy to 7, and do not let a global
`typescript-language-server` shadow it — Hermes treats an existing server on
`PATH` as "already installed" and will skip installing its pinned pair.

## Trust model

LSP is gated on **git workspace detection** and workspace trust. Hermes trusts
the git worktree of the directory it was launched in, or a directory listed under
`lsp.trusted_workspaces` (and anything below it). Untrusted workspaces skip
servers that execute project code, including `rust-analyzer` and `gopls`.

Do not add broad paths such as `$HOME` to `lsp.trusted_workspaces`:
`rust-analyzer` runs `cargo check`, which executes build scripts and proc macros
from the checkout.

## Checks

```sh
hermes lsp status
hermes lsp which rust-analyzer
hermes lsp restart          # tear down clients; the next edit re-spawns
hermes lsp install <server> # recipes: pyright, gopls, yaml-language-server, ...
```

`install_strategy` is `auto`, so a missing recipe is provisioned on demand.

## Known limits

- **Not verified end-to-end:** a real `write_file`/`patch` cycle emitting
  `lsp_diagnostics`. That needs an edit inside a git repository.
- **`rust-analyzer` is standalone**, not a rustup component, because
  `/usr/local/rustup` is root-owned. `rustup update` does not refresh it.
- HTML/CSS/JSON servers are **not** registered by Hermes and were removed. They
  would need explicit `lsp.servers` entries and are of low value for agent edits.
