# Models & presets

Ana works with any chat model Ollama can serve, and adapts to each one
through a **model profile**: probed capabilities merged with a per-model
preset.

## Model selection

When `OLLAMA_DEFAULT_MODEL` is unset, Ana picks a default that fits your
hardware. The budget is the discrete GPU's VRAM when an NVIDIA/AMD card is
detected (that's what limits GPU offload), otherwise total system RAM
(Apple unified memory or a CPU-only box). Model weights are budgeted at
roughly **60%** of that so the KV cache, your context, the background
model, and the OS still fit — a model that barely fits runs slower than a
smaller one with headroom.

| Your RAM / VRAM | Recommended model | Pull command |
|----------|------------------|--------------|
| 8 GB | qwen3.5:4b | `ollama pull qwen3.5:4b` |
| 16 GB | qwen3.5:9b | `ollama pull qwen3.5:9b` |
| 24 GB | devstral-small-2:24b | `ollama pull devstral-small-2:24b` |
| 32 GB+ | qwen3.6:27b | `ollama pull qwen3.6:27b` |

Inspect what Ana sees:

```bash
ana models list             # all installed models with profiles
ana models info qwen3.5:9b  # full effective profile for one model
```

Switch mid-session with `/model` in chat.

## Model roles

Beyond the main chat model, Ana uses two optional supporting roles — both
resolved automatically from your installed models, both overridable:

| Role | Used for | Default | Override |
|---|---|---|---|
| **Background** | Compaction summaries, lesson distillation, watch reviews | Smallest installed chat model ≥ 4B params | `ANA_BACKGROUND_MODEL` |
| **Escalation** | Format-repair retries; auto-escalate after repeated verification failures | Largest installed model | `ANA_ESCALATION_MODEL` |

## Model presets

Each preset is a YAML file that overrides auto-detected values for a
specific model. Ana merges: probed values ← packaged preset ←
`~/.ana/presets/` user override (later wins on non-null keys), then
computes `effective_context = context_limit * 0.80`.

```yaml
# ~/.ana/presets/my-model.yaml
display_name: "My Model 7B"
context_limit: 32768
prompt_template_family: qwen     # qwen | llama | mistral | chatml
supports_native_tools: true
tool_strategy: native            # native | constrained | prompted
recommended_temperature: 0.15
tier: light                      # light | mid | high
parameter_count_b: 7.0
ram_required_gb: 6.0
notes: "Custom preset for my fine-tuned model."

# Optional per-model samplers (env vars still win — see Settings):
sampling:
  min_p: 0.05
  repeat_penalty: 1.05

# Grammar-constrain the main call for weak models that can't reliably emit
# a tool call first-try (only used for tool_strategy: constrained):
constrain_main_call: false
```

**File naming:** `{model-name-with-colon-as-dash}.yaml` — model `myllm:7b`
→ file `myllm-7b.yaml`, placed in `~/.ana/presets/`.

### Key fields

| Field | Meaning |
|---|---|
| `context_limit` | Advertised context window; Ana budgets 80% of it |
| `supports_native_tools` | Whether the model does native (API-level) tool calling |
| `tool_strategy` | `native` (preferred), `constrained` (grammar-constrained JSON), or `prompted` |
| `tier` | Rough capability class used in picker UI and defaults |
| `sampling` | Per-model sampler overrides |

## Non-Ollama backends

Ana can point at any OpenAI-compatible inference server instead of Ollama
(`ANA_BACKEND`, plus `ANA_BACKEND_BASE_URL` when the server isn't on its
default port — see [Settings](settings.md#inference-backend)):

- **LM Studio**: `ANA_BACKEND=lmstudio`
- **llama.cpp** (`llama-server`): `ANA_BACKEND=llamacpp`
- **vLLM or other OpenAI-compatible servers**: `ANA_BACKEND=openai_compat`

### Speculative decoding (throughput)

Speculative decoding runs a small "draft" model ahead of the main model for
a ~1.5–2× speedup on long code output (code patterns hit >80% draft
acceptance), with no change to output quality. It is configured on the
**inference server**, not in Ana — Ana connects as a client and benefits
transparently.

- **llama.cpp**: launch with a draft model, e.g.
  `llama-server -m qwen3-8b.gguf --model-draft qwen3-0.6b.gguf`.
- **vLLM**: enable the engine's own speculation config (e.g.
  `--speculative-model`).
- **Ollama**: not currently exposed as a client option.

Pick a **vocab-matched** draft (same tokenizer family), a few times smaller
than the target — e.g. Qwen3 0.6B → Qwen3 8B. Gains are largest on long,
low-temperature generations; benchmark before committing.

## Related

- [Settings](settings.md) — decoding-quality env vars
- [Troubleshooting](../reference/troubleshooting.md#ollama-problems) — cold
  loads, missing models, derailing output
