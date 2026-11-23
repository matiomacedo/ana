# Models & presets

Ana talks to one **provider** at a time: a model server on your computer
(Ollama, LM Studio, llama.cpp or any OpenAI-compatible server such as vLLM)
or a cloud API (Anthropic, OpenAI, Google Gemini and others, with your own
key). It adapts to each model through a **model profile**: probed or listed
capabilities merged with a per-model preset.

## Providers

| Provider | Id (`backend`) | Kind | Key setting | Key environment variable |
|---|---|---|---|---|
| Ollama | `ollama` | local | — | — |
| LM Studio | `lmstudio` | local | `backend_api_key` | `ANA_BACKEND_API_KEY`, `OPENAI_COMPAT_API_KEY` |
| llama.cpp (`llama-server`) | `llamacpp` | local | `backend_api_key` | `ANA_BACKEND_API_KEY`, `OPENAI_COMPAT_API_KEY` |
| OpenAI-compatible (vLLM…) | `openai_compat` | local | `backend_api_key` | `ANA_BACKEND_API_KEY`, `OPENAI_COMPAT_API_KEY` |
| Anthropic | `anthropic` | cloud | `anthropic_api_key` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | cloud | `openai_api_key` | `OPENAI_API_KEY` |
| Google Gemini | `google` | cloud | `google_api_key` | `GEMINI_API_KEY`, then `GOOGLE_API_KEY` |
| OpenRouter | `openrouter` | cloud | `openrouter_api_key` | `OPENROUTER_API_KEY` |
| Groq | `groq` | cloud | `groq_api_key` | `GROQ_API_KEY` |
| DeepSeek | `deepseek` | cloud | `deepseek_api_key` | `DEEPSEEK_API_KEY` |
| xAI | `xai` | cloud | `xai_api_key` | `XAI_API_KEY` |
| Mistral | `mistral` | cloud | `mistral_api_key` | `MISTRAL_API_KEY` |
| Together AI | `together` | cloud | `together_api_key` | `TOGETHER_API_KEY` |
| Fireworks | `fireworks` | cloud | `fireworks_api_key` | `FIREWORKS_API_KEY` |
| Cerebras | `cerebras` | cloud | `cerebras_api_key` | `CEREBRAS_API_KEY` |

Pick one with the `backend` setting (`ANA_BACKEND`), in `/settings`, in the
Mac app's **Settings → Provider**, or inline:

```text
/settings backend anthropic
/settings anthropic_api_key sk-ant-...
```

**Keys.** An environment variable wins over the saved setting; when one is
set, `/settings` and the Mac app show the key as locked. A saved key lives in
`~/.ana/settings.json`, written readable only by you. Ana never shows a key
back: the settings API, `/settings` and the Mac app show only `set …1234`
(the last four characters). Each cloud provider keeps its own key, so you can
switch back and forth without typing it again. Saving an empty value removes
a saved key.

**Hot switching.** A change to `backend`, `backend_base_url` or an API key
takes effect on the next message, with no backend restart. Ana lists the new
provider's models, moves `default_model` to one it serves (a cloud provider's
default preset; on a local server the usual selection), and forgets anything
cached for the old provider. `/settings backend <id>` prints how many models
the provider lists and whether it accepted the key. `ana models list` and the
`/model` picker show only the active provider's models. A session keeps the
model it chose; if that model belongs to another provider, Ana asks you to pick
one the active provider serves.

**Which cloud models.** For a cloud provider, Ana lists the models that have
a preset (see [Presets](#model-presets)) *and* that your account can use; the
provider's model listing also checks the key. A refused key shows as an error
in `/settings backend <id>`, `ana doctor` and the Mac app.

**Memory search with a cloud provider.** Embeddings (lessons, code search)
never go to a cloud API. They use the active server when it is local, and a
local Ollama otherwise. Without Ollama, lessons and the code index are off and
`ana doctor` says so; chat works either way.

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

The table above applies to Ollama. A cloud provider's default model is its
`default: true` preset.

Inspect what Ana sees:

```bash
ana models list             # the active provider's models with profiles
ana models info qwen3.5:9b  # full effective profile for one model
```

Switch mid-session with `/model` in chat.

## Context window

Three different numbers are involved, and it's worth keeping them apart:

| Number | What it is | Where you see it |
|---|---|---|
| **Trained limit** | The context the model was actually trained for, read from Ollama | `Max` column in `ana models list`, `Context:` in `ana models info` |
| **Allocated window** | What Ana asks the backend to load (Ollama's `num_ctx`) | `Context` column, `Allocated:` in `ana models info` |
| **Prompt budget** | 80% of the allocated window; the rest is headroom for the reply | `/context` in chat |

Ana always sends an explicit `num_ctx`. Without one Ollama falls back to its
own small default and silently truncates long conversations, and a value that
changes between calls forces a model reload that throws away the KV cache.

You decide what that value is, in this order:

| Precedence | Source |
|---|---|
| 1 | `ANA_OLLAMA_NUM_CTX` — escape hatch; `0` sends no `num_ctx` at all |
| 2 | `context_length` in `~/.ana/settings.json` (editable in `/settings`) |
| 3 | `OLLAMA_CONTEXT_LENGTH` — your own Ollama server configuration |
| 4 | *auto*: 32K, or less when the trained limit or your memory is smaller |

A value you set is honoured even when it exceeds the memory estimate — Ana
warns rather than silently shrinking it (`ana doctor` surfaces the warning).
Only the auto value is capped. Any source is clamped to the model's trained
limit. `ana models info` names whichever source won:

```
Context:   262,144 tokens (probe)
Allocated: 32,768 tokens · 26,214 for the prompt (auto, Ana's 32K default)
```

!!! note "Bigger is not free"
    The KV cache is pre-allocated, so a large window costs memory whether or
    not you fill it. Measured on `qwen3.5:4b`, a 32K window uses about 2 GB and
    a 192K window about 10 GB, with no change in load time or generation speed.
    To go above 32K, set `context_length` or `ANA_OLLAMA_NUM_CTX`.

Changing `context_length` takes effect on the next backend restart: the
context budget Ana plans against is fixed when the model profile is built.

On LM Studio, llama.cpp and OpenAI-compatible servers, the trained limit is
whatever the server reports. If it reports nothing, Ana uses its default profile,
so set `context_length` to match what the server actually loaded.

## Model roles

Beyond the main chat model, Ana uses two optional supporting roles — both
resolved automatically, both overridable:

| Role | Used for | Default | Override |
|---|---|---|---|
| **Background** (helper) | Session titles, compaction summaries, lesson distillation, watch reviews | Local provider: the session's own model, so no second model loads. Cloud provider: its cheap `background: true` preset (for example Claude Haiku on Anthropic) | `background_model` (`ANA_BACKGROUND_MODEL`) |
| **Escalation** | Format-repair retries; auto-escalate after repeated verification failures | Largest installed model that fits in memory. Off Ollama, none unless you set one | `escalation_model` (`ANA_ESCALATION_MODEL`) |

`background_provider` (`ANA_BACKGROUND_PROVIDER`) says where the helper runs:
`active` (the default: the active provider) or `ollama`, which keeps helper
calls on a local Ollama model even while a cloud provider answers chat, so they
cost nothing. With `ollama` and no `background_model`, Ana picks the smallest
installed Ollama chat model. In the Mac app, **Settings → Provider → Helper
model** offers the provider's models and the installed Ollama models in one
menu and sets both settings.

## Model presets

Each preset is a YAML file that overrides auto-detected values for a
specific model. Ana merges: probed values ← packaged preset ←
`~/.ana/presets/` user override (later wins on non-null keys).

```yaml
# ~/.ana/presets/my-model.yaml
display_name: "My Model 7B"
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

**File naming:** the model name with `:` and `/` as `-` and `.` as `_` —
model `myllm:7b` → `myllm-7b.yaml`, placed in `~/.ana/presets/`.

### Folder layout

```text
ana/adapters/presets/              # packaged with Ana
├── qwen3_5-9b.yaml                # local models: flat
├── anthropic/                     # cloud models: one folder per provider id
│   ├── claude-sonnet-5-5.yaml
│   └── claude-haiku-5-5.yaml
├── openai/
└── ...
~/.ana/presets/                    # yours; same layout, wins over the packaged file
├── myllm-7b.yaml
└── anthropic/claude-sonnet-5-5.yaml
```

For a model of provider `<id>`, Ana looks in `presets/<id>/` before the flat
folder, and in `~/.ana/presets/` before the packaged presets. A cloud preset
names the exact API id and its provider, and says how the model thinks:

```yaml
# presets/anthropic/claude-haiku-5-5.yaml
model_id: claude-haiku-5-5       # exact API model id (required for cloud)
provider: anthropic              # must equal the folder name
display_name: Claude Haiku 5.5
context_limit: 1000000
effective_context: 200000        # what Ana plans the prompt against
max_output_tokens: 128000
supports_native_tools: true
tool_strategy: native
accepts_temperature: false       # the API rejects samplers
thinking:
  style: anthropic_adaptive      # none | ollama_bool | ollama_level | openai_effort |
                                 # anthropic_adaptive | gemini_level | gemini_budget | openrouter
  off_mode: disabled             # what Off sends; null = can't turn off, Off acts as Low
background: true                 # the provider's helper model (one per provider)
cheap: true
notes: "... verified 2026-11-20 https://..."
```

Exactly one preset per cloud provider has `default: true` (its default chat
model) and one has `background: true` (its helper model).

### Key fields

| Field | Meaning |
|---|---|
| `context_limit` | The model's trained context. Read from Ollama — only set this to correct a model that misreports it, or to record a smaller *usable* context you measured with `ana models bench`. To change how much Ana loads, use `context_length` instead (see [Context window](#context-window)) |
| `supports_native_tools` | Whether the model does native (API-level) tool calling |
| `tool_strategy` | `native` (preferred), `constrained` (grammar-constrained JSON), or `prompted`. Without one, Ana uses `native` when the backend reports tool support; otherwise `constrained` on Ollama and `prompted` elsewhere |
| `tier` | Rough capability class used in picker UI and defaults |
| `sampling` | Per-model sampler overrides |
| `thinking` | How the model's reasoning is controlled; absent or `style: none` means [thinking effort](#thinking-effort) is ignored for it |

## Thinking effort

How hard a model thinks before it answers, on models whose preset has a
`thinking` block. The levels are **Default** (the model's own behaviour,
the default), **Off**, **Low**, **Medium** and **High**. Ana translates the
level into each provider's own control (an effort level, a token budget, or
thinking on/off). A model that can't stop thinking treats Off as Low.

- **Globally:** the `thinking_effort` setting (`ANA_THINKING_EFFORT`):
  `default` \| `off` \| `low` \| `medium` \| `high`.
- **Per session:** `/effort <level>` in chat, or the effort menu next to the
  model picker in the Mac app; it wins over the global setting for that
  session. The menu is hidden for models that can't think.

Higher effort is slower and, on cloud providers, costs more output tokens.

## Local servers other than Ollama

Ana can point at any OpenAI-compatible inference server instead of Ollama
(`backend`, plus `backend_base_url` when the server isn't on its default port
— see [Settings](settings.md#provider)):

- **LM Studio**: `backend = lmstudio` (default `http://localhost:1234`)
- **llama.cpp** (`llama-server`): `backend = llamacpp` (default `http://localhost:8080`)
- **vLLM or other OpenAI-compatible servers**: `backend = openai_compat` (default `http://localhost:8000`)

`backend_base_url` applies to the active provider only, so switching
provider never sends its address to another one.

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
