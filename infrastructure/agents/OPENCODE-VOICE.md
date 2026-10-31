# OpenCode mobile voice research — 31 October 2026

Research only: no configuration mutation, provider session, recording, API-key
change or OpenCode restart. Current installed server is2.2.5. Mobile client
identity/version is awaiting owner clarification; do not infer client capabilities
from the server version or from old v1 articles.

## Confirmed server capabilities

Read the pinned2.2.5 core Voice service, experimental realtime engine registry,
protocol routes and app voice composer. Queried only GET
/api/experimental/voice/models in the already-live Homelab location, explicitly
setting x-opencode-directory to avoid initializing extra MCP locations.

The current response advertises gpt-live-1 via the opencode provider as available
and default. This is credential availability, not an audio handshake, microphone,
iPhone-client or end-to-end voice test. The current response lists
openai/gpt-realtime-2.1, xai/grok-voice-3.0 and google/gemini-3.8-live unavailable.
The provider registry has no Groq realtime engine. Existing OpenCode Console
credentials can broker hosted GPT-Live; direct provider alternatives require
appropriate server API credentials. Hosted GPT-Live is billed to the connected
OpenCode workspace; do not claim it is included with Claude Max/OpenCode Go.
ChatGPT subscription sign-in is not an OpenAI API key for this route.

The shared app voice-call button in this pinned source is gated to desktop,
non-production builds and an experiment toggle. Do not claim that merely setting
a server key enables it in every browser/mobile client. An upstream iOS issue
reports separate composer dictation and a Settings→Voice screen in an App Store
client. That report is evidence of that client's UI, not verification of the
owner's exact app or latest build.

## Groq speech-to-text is a separate input path

Groq supports OpenAI-compatible audio transcription at
https://api.groq.com/openai/v1/audio/transcriptions using whisper-large-v3 and
whisper-large-v3-turbo. These are transcription models, not drop-in replacements
for OpenAI Realtime/WebRTC. Adding GROQ_API_KEY to the OpenCode service does not
add a built-in mobile microphone or change Voice.models to Groq.

A possible custom path is: phone microphone → authenticated transcription
endpoint on the homelab → Groq Whisper → text returned to the phone's draft →
normal OpenCode request using its selected coding model. Keep the Groq key on
the server if implementing this; phone app/frontend must actually support audio
capture/upload and receiving/inserting the transcript. Groq remains a cloud
service. A terminal plugin that records the server's audio device does not
capture a remote phone's microphone. Community TUI plugins/userscripts are
client-specific and not assumed compatible with official iOS or OpenCode2.2.5.

## Next step

Identify the exact mobile app and version. First check its native voice/settings
against the already-advertised hosted GPT-Live route. For speech-to-text only,
check whether it permits a custom STT endpoint before implementing a separate
Groq service. Native phone keyboard dictation is also a client-side option.
No plugin/service/key deployment was performed during research.

## Sources

- [Pinned server Voice service](https://github.com/anomalyco/opencode/blob/v2.2.5/packages/core/src/voice.ts)
- [Pinned realtime engine registry](https://github.com/anomalyco/opencode/blob/v2.2.5/packages/ai/src/experimental/realtime.ts)
- [Pinned voice API routes](https://github.com/anomalyco/opencode/blob/v2.2.5/packages/protocol/src/groups/voice.ts)
- [Pinned shared app call-button gates](https://github.com/anomalyco/opencode/blob/v2.2.5/packages/app/src/voice/composer.tsx)
- [Upstream iOS dictation issue56973](https://github.com/anomalyco/opencode/issues/56973)
- [Groq speech-to-text documentation](https://console.groq.com/docs/speech-to-text)
