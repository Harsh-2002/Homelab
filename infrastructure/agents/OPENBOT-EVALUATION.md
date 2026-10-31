# OpenBot comparison — research, 31 October 2026

Product evaluated: openbot.run / nightly-labs/openbot. No installation, imports,
credentials, runtime changes or agent deployment authorized/performed. Assessment
uses upstream docs/source and App Store release notes, not hands-on benchmarking.
Context7 had no exact OpenBot entry; primary sources were used instead.

## Fit for this homelab

OpenBot is a candidate for an app-based team workspace around native Codex,
Claude Code and other coding runtimes. Independent agent workspaces, persistent
queues, shared channels, delegation, file transfer and browser/computer control
are documented. Desktop, iPhone/Android and web clients connect to a host. It
supports a self-hosted Linux server and Docker; phone use still needs the host
running. Default remote hosting connects through an OpenBot account/control
plane; local-first should not be equated with cloud-independent or offline-only.

Hermes remains the established personal-assistant/automation runtime here, with
existing OpenViking, tools, messaging and provider setup. Its upstream features
include persistent memory/skills, session search, cron delivery and a messaging
gateway. OpenClaw is another gateway-oriented assistant with channels, multiple
agents, memory, scheduled automation and official phone node apps; mobile apps
are not an OpenBot-exclusive feature. No performance/intelligence winner is
established by this research; underlying models, runtime and tools all matter.

OpenBot personal/noncommercial use on one's own computer is currently free.
AI provider subscription/API usage remains separate; hosted OpenBot servers and
commercial licenses are separate paid products. Its license is source-available
PolyForm Noncommercial1.0.0, not the MIT license used by Hermes/OpenClaw. Do not
interpret working alone as automatically noncommercial use. No legal opinion or
future pricing guarantee is implied.

OpenBot's README labels it a development preview and states that current agents
have danger-full-access/approvalPolicy never after first-launch consent. This
is a concrete runtime property to consider before giving it homelab credentials.
Do not assume independent workspaces provide security isolation.

## Mobile voice relevance

The iOS App Store release1.4.3 advertises voice conversations and voice settings.
Current mobile source lists speech recognition engines system, on-device
Parakeet and ElevenLabs Scribe, plus reply voices Supertonic/on-device and
ElevenLabs. No Groq recognizer is in that settings type. These are current source/
release-note capabilities, not a microphone test on the owner's phone. Native
voice may make it useful for the owner's mobile workflow without a Groq add-on.

## Hermes import is selective

The importer creates OpenBot agents from Hermes profiles, carrying supported
persona, MEMORY.md/USER.md entries, custom skills and schedules as routines.
Full chat history, login credentials, bundled skills and some job types are not
transferred. Folder-imported MCP settings arrive disabled with sensitive values
cleared; ZIP import excludes MCP settings. Existing source profiles are preserved.
Our external OpenViking database/provider integration is not established by that
file import. Shared memory/tool identity and recall/capture need explicit
configuration and verification before adopting OpenBot as another harness.

Recommendation: retain Hermes for current personal/homelab automation. Evaluate
OpenBot separately if unified phone access and agent-team workflows solve a real
need. A small isolated build/review exercise can test fit without migrating the
existing setup. Do not add unbounded agents/browser processes to the already
memory-constrained dev VM; actual peak memory must be measured if deployed.

## Primary sources

- [OpenBot README and preview status](https://github.com/nightly-labs/openbot)
- [Pricing](https://openbot.run/pricing)
- [License](https://github.com/nightly-labs/openbot/blob/main/LICENSE)
- [Self-hosted server](https://github.com/nightly-labs/openbot/blob/main/docs/self-hosted-server.md)
- [Hermes import guide](https://openbot.run/guides/import-hermes-agents)
- [iPhone release notes](https://apps.apple.com/us/app/openbot-run/id6807024266)
- [Mobile voice settings](https://github.com/nightly-labs/openbot/blob/main/apps/mobile/src/features/voice/model/voice-settings.ts)
- [Hermes upstream features](https://github.com/NousResearch/hermes-agent)
- [OpenClaw documentation](https://docs.openclaw.ai/)
- [OpenClaw official iPhone app](https://docs.openclaw.ai/platforms/ios)
