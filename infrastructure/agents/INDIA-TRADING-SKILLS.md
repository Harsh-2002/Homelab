# India trading skills

Third-party Agent Skills pack for NSE/BSE analysis, installed 5 November 2026 at
the owner's request.

- Source: `github.com/Shubhamkumartrichy/claude-trading-skills-india`
- Commit: `ef36e75` (2 November 2026), MIT, at install time 41 stars
- 29 skills, 16 stdlib-only Python calculators, no runtime dependencies
- Optional `yfinance` only for live prices; every calculator works offline from CSV

## Install layout

```text
~/.local/share/india-trading-skills/          git clone (update with git pull)
~/.agents/skills/<skill>            ->        symlink to the clone (canonical)
~/.hermes/skills/<skill>            ->        ~/.agents/skills/<skill>
~/.claude/skills/<skill>            ->        ~/.agents/skills/<skill>
OpenCode                                       reads ~/.agents/skills directly
```

All 29 must live side by side: several skills call scripts in a sibling, for
example `rsi-divergence` runs `../technical-analysis/scripts/ta.py`.

Update with:

```sh
git -C ~/.local/share/india-trading-skills pull --ff-only
```

Symlinks keep pointing at the clone, so no relinking is needed.

## Security review (before install)

- No hooks, no shell scripts, no `subprocess`, `eval`, `exec` or network
  libraries in any Python file.
- Only URLs in code are broker pricing pages and OOXML schema namespaces.
- `.claude-plugin/plugin.json` is metadata only — no hooks or commands.
- Scripts read local CSV or optional yfinance; they do not write outside the
  working directory.

## Skills

`india-market-analyst` is the router; the rest cover technical analysis,
multi-timeframe, RSI divergence, Fibonacci, breakouts, momentum, market regime,
breadth, sector rotation, FII/DII flows, F&O options, options strategies, pair
trading, backtesting, position sizing, stops, trailing stops, risk-reward,
trading costs, tax, market structure, results season, IPOs, fundamentals,
portfolio review, trading discipline and broker integration.

## Broker MCP: Zerodha Kite (hosted)

Configured in OpenCode, Hermes and Claude Code as a remote HTTP MCP:

```text
https://mcp.kite.trade/mcp
```

The server exposes **22 tools**, including `place_order`, `modify_order`,
`cancel_order` and the GTT tools. This is broader than the pack's October 2026
note, which said the hosted server only allowed GTT orders — verify capabilities
before relying on that claim.

Authentication is not OAuth at the transport level. The server is reachable
without credentials; the first data call returns
`Please log in first using the login tool`. The `login` tool returns a Kite login
URL for the owner to complete, and the session then holds the credentials.

No credentials are stored on this host: `oauth` is off, there are no headers, and
nothing is saved to Git.

### Risk note

Once logged in, any agent with this MCP can place real orders on the owner's
Zerodha account. The `broker-integration` skill defines a mandatory
confirmation protocol, but that is instruction-level, not a technical control.
For stricter containment, self-host `github.com/zerodha/kite-mcp-server` with
`EXCLUDED_TOOLS` to drop the order tools and keep read-only market data.

## Verification

```sh
opencode mcp list | grep kite          # ✓ connected
hermes mcp test kite                   # 22 tools discovered
claude mcp list | grep kite            # ✔ Connected
```

An unauthenticated `get_profile` returns the login prompt, which confirms the
transport works and authentication is still pending.
