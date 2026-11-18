import { Plugin } from "@opencode/plugin"

type ModelSpec = {
  variants: readonly string[]
  defaultVariant: string
}

// Approved model catalog. Models with thinking levels carry an explicit default
// variant, used when a caller names the model without one. Models that expose no
// thinking levels (the OpenCode free models) have an empty variants list.
const CATALOG: Record<string, ModelSpec> = {
  // Chinese models: max by default.
  "opencode-go/deepseek-v4.1-flash": { variants: ["low", "high", "max"], defaultVariant: "max" },
  "opencode-go/glm-5.3-flash": { variants: ["low", "high", "max"], defaultVariant: "max" },
  "opencode-go/minimax-m3.1-flash": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "max" },
  "opencode-go/qwen4-max": { variants: ["none", "low", "high", "xhigh"], defaultVariant: "xhigh" },
  // OpenAI Codex: medium by default; high for demanding work.
  "openai/gpt-6.2-astra": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "openai/gpt-6.2-sol": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "openai/gpt-6-astra": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "openai/gpt-6.1-sol": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "openai/gpt-6.1-terra": { variants: ["none", "low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "openai/gpt-6-luna": { variants: ["none", "low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  // Claude Agent: medium by default; high for demanding work.
  "claude-agent/claude-opus-5-5": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "claude-agent/claude-sonnet-5-5": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "claude-agent/claude-haiku-5-5": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  "claude-agent/claude-fable-5-2": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "medium" },
  // OpenCode free models (provider `opencode`, no credits needed, time-limited and
  // rotating). Variants below were read from the live server on 2026-11-18; some
  // models (big-pickle, iceman, longcat, mimo, nemotron-lightning) have none and
  // take no #variant. Privacy classes are in skills/model-catalog/SKILL.md: only the
  // zero-retention ones may see private homelab work.
  "opencode/glm-5.3-flash-free": { variants: ["low", "high", "max"], defaultVariant: "max" },
  "opencode/deepseek-v4.1-flash-free": { variants: ["low", "high", "max"], defaultVariant: "max" },
  "opencode/hy4-flash-free": { variants: ["none", "high"], defaultVariant: "high" },
  "opencode/beam-free": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "max" },
  "opencode/longcat-2.5-free": { variants: [], defaultVariant: "" },
  "opencode/mimo-v2.6-flash-free": { variants: [], defaultVariant: "" },
  "opencode/big-pickle": { variants: [], defaultVariant: "" },
  "opencode/iceman-free": { variants: [], defaultVariant: "" },
  "opencode/inkling-2-small-free": { variants: ["none", "minimal", "low", "medium", "high", "max"], defaultVariant: "max" },
  "opencode/flint-40b-free": { variants: ["low", "medium", "high", "xhigh", "max"], defaultVariant: "max" },
  "opencode/nemotron-3.5-lightning-free": { variants: [], defaultVariant: "" },
  "opencode/nemotron-3.5-super-vl-free": { variants: ["none", "minimal", "low", "medium", "high", "xhigh"], defaultVariant: "xhigh" },
}

const FALLBACK = "opencode-go/deepseek-v4.1-flash#max"
const ALLOWED_BASES = new Set(Object.keys(CATALOG))

function splitModel(ref: string): { base: string; variant?: string } {
  const hash = ref.indexOf("#")
  if (hash === -1) return { base: ref }
  return { base: ref.slice(0, hash), variant: ref.slice(hash + 1) }
}

// Return a model reference that is guaranteed to carry a supported variant.
// Unknown models return undefined; the caller decides the fallback.
function normalizeModel(ref: string): string | undefined {
  const { base, variant } = splitModel(ref)
  const spec = CATALOG[base]
  if (!spec) return undefined
  // A model without thinking levels takes no variant at all.
  if (spec.variants.length === 0) return base
  if (variant === undefined || !spec.variants.includes(variant)) {
    return `${base}#${spec.defaultVariant}`
  }
  return `${base}#${variant}`
}

export default Plugin.define({
  id: "model-allowlist",
  async setup(ctx) {
    // Keep the model picker inside the approved set. Variants are nested in
    // each model, so the base reference is the right key here.
    await ctx.model.transform((editor) => {
      for (const model of editor.list()) {
        const ref = `${model.providerID}/${model.id}`
        if (!ALLOWED_BASES.has(ref)) {
          editor.remove(model.providerID, model.id)
        }
      }
    })

    // Defense in depth: a subagent call cannot escape the catalog, and every
    // explicit model reference carries a valid thinking level. An unspecified
    // model is left alone so the subagent's configured default applies.
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "subagent") return
      const input = event.input as { model?: string }
      if (typeof input.model === "string") {
        input.model = normalizeModel(input.model) ?? FALLBACK
      }
    })

    // Normalize the model on every request as well. This covers a model picked
    // directly in the session picker, which bypasses the subagent hook.
    // Title generation is skipped so a cheap background request does not get
    // promoted to #max.
    await ctx.session.hook("experimental.model.resolve", (event) => {
      if (event.kind === "title") return
      const ref = `${event.model.providerID}/${event.model.id}`
      const spec = CATALOG[ref]
      if (!spec || spec.variants.length === 0) return
      if (event.model.variant === undefined || !spec.variants.includes(event.model.variant)) {
        event.model = { ...event.model, variant: spec.defaultVariant }
      }
    })
  },
})
