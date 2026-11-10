import { Plugin } from "@opencode/plugin"

const ALLOWED = new Set([
  "opencode-go/deepseek-v4.1-flash",
  "opencode-go/glm-5.3-flash",
  "opencode-go/minimax-m3.1-flash",
  "openai/gpt-6-astra",
  "openai/gpt-6.1-sol",
  "openai/gpt-6.1-terra",
  "openai/gpt-6-luna",
  "claude-agent/claude-opus-5",
  "claude-agent/claude-sonnet-5",
  "claude-agent/claude-haiku-4-5-20251001",
])
const FALLBACK = "opencode-go/deepseek-v4.1-flash"

export default Plugin.define({
  id: "model-allowlist",
  async setup(ctx) {
    // Keep the model picker inside the approved set.
    await ctx.model.transform((editor) => {
      for (const model of editor.list()) {
        const ref = `${model.providerID}/${model.id}`
        if (!ALLOWED.has(ref)) {
          editor.remove(model.providerID, model.id)
        }
      }
    })

    // Defense in depth: a stale or hand-written subagent call cannot escape
    // the catalog by passing an unapproved model reference.
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "subagent") return
      const input = event.input as { model?: string }
      // No model means "use the subagent's configured default".
      if (typeof input.model === "string" && !ALLOWED.has(input.model)) {
        input.model = FALLBACK
      }
    })
  },
})
