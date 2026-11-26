# Models & presets

Ana runs models on **providers**: model servers on your computer (Ollama,
LM Studio, llama.cpp or any OpenAI-compatible server such as vLLM) and cloud
APIs (Anthropic, OpenAI, Google Gemini and others, with your own key). Each
[model role](#model-roles) — the main chat model, subagents, the helper,
escalation and embeddings — picks its own provider and model, so you can mix
them. Ana adapts to each model through a **model profile**: probed or listed
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

The `backend` setting (`ANA_BACKEND`) is the **main provider**: what a
session runs on unless it picks a model elsewhere. Set it in `/settings`, in
the Mac app's **Settings → Provider**, or inline:

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

**Hot switching.** A change to any role's provider, a server's URL or an
API key takes effect on the next message, with no backend restart. For a new
main provider Ana lists its models, moves `default_model` to one it serves (a
cloud provider's default preset; on a local server the usual selection), and
forgets anything cached for the old one. `/settings backend <id>` prints how
many models the provider lists and whether it accepted the key.

**Picking a model.** `ana models list`, `/model` and the Mac app's model
picker list the models of every provider a role uses, the main provider's
first (the Mac app groups them under provider names). A session remembers the
provider of the model it picked, so one session can run on DeepSeek while the
main provider stays Anthropic; the Mac app then shows the model as
`deepseek-chat · DeepSeek`.

**Which cloud models.** For a cloud provider, Ana lists the models that have
a preset (see [Presets](#model-presets)) *and* that your account can use; the
provider's model listing also checks the key. A refused key shows as an error
in `/settings backend <id>`, `ana doctor` and the Mac app.


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
ana models list             # every provider's models with profiles
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

Every role is a provider + model pair. Each provider defaults to `ollama`;
each model defaults to something sensible on its provider.

| Role | Used for | Provider setting | Model setting | Model when unset |
|---|---|---|---|---|
| **Main** (orchestrator) | Your sessions, and the orchestrator that spawns subagents | `backend` | `default_model` | Picked by memory on Ollama; the provider's default preset in the cloud |
| **Subagents** | Every subagent an orchestrating session spawns | `subagent_provider` | `subagent_model` | The session's model when it runs on that provider, else the provider's default |
| **Helper** (background) | Session titles, compaction summaries, lesson distillation, watch reviews | `background_provider` | `background_model` | Cloud: the provider's cheap `background: true` preset (for example Claude Haiku). Local: the session's model when it runs there, so no second model loads, else the smallest Ollama model |
| **Escalation** | Format-repair retries; auto-escalate after repeated verification failures | `escalation_provider` | `escalation_model` | On Ollama, the largest installed model that fits in memory; elsewhere none unless you set one |
| **Embeddings** | Lessons and code search | `embedding_provider` | `embedding_model` | The provider's embedding model (below) |

Subagents get one pick for all of them: the orchestrator can't choose another
model or provider for a subagent it spawns. In the Mac app each role has its
own provider and model menus under **Settings → Provider**; in the terminal
use `/settings`.

### Example: Opus as orchestrator, DeepSeek for subagents

```text
/settings backend anthropic
/settings anthropic_api_key sk-ant-...
/settings default_model claude-opus-5-5
/settings subagent_provider deepseek
/settings deepseek_api_key sk-...
/settings subagent_model deepseek-chat
```

Opus plans and delegates; every subagent runs on DeepSeek. The helper and
escalation roles stay on Ollama until you move them too.

### Embeddings

`embedding_provider` is one of the local servers, `openai`
(`text-embedding-3-small`), `google` (`gemini-embedding-001`), `mistral`
(`mistral-embed`), `fireworks` (`fireworks/qwen3-embedding-8b`),
`openrouter` (`openai/text-embedding-3-small`), or `off`. Ollama defaults to
`qwen3-embedding:0.6b`; LM Studio, llama.cpp and other OpenAI-compatible
servers need `embedding_model` set. Anthropic, Groq, DeepSeek, xAI, Together
and Cerebras have no embeddings endpoint. With `off`, lessons and the code
index are off; chat and the repo map work as usual.

!!! warning "Changing the embedding provider or model deletes saved vectors"
    Vectors from one embedding model can't be searched with another. Changing
    `embedding_provider` or `embedding_model` while lessons or code-index
    chunks are saved deletes them, so Ana asks first and says how many would
    go. The code index rebuilds as you work; lessons
    can't be recovered. Ana doesn't re-embed them automatically, because on a
    cloud provider every re-embedded chunk is a paid API call.

### Running with no local server

Put every role on a cloud provider and either a cloud embedding provider or
`off`, and Ana never needs Ollama or any other local server: `ana doctor`
skips its Ollama checks, and `ana chat` warns only about a role whose
provider it can't reach.

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

Any role can run on an OpenAI-compatible inference server instead of Ollama.
Each local server has its own address setting, so several can be in use at
once (see [Settings](settings.md#provider)):

- **Ollama**: `ollama_base_url` (default `http://localhost:11434`)
- **LM Studio**: `lmstudio`, `lmstudio_base_url` (default `http://localhost:1234`)
- **llama.cpp** (`llama-server`): `llamacpp`, `llamacpp_base_url` (default `http://localhost:8080`)
- **vLLM or other OpenAI-compatible servers**: `openai_compat`, `openai_compat_base_url` (default `http://localhost:8000`)

`backend_base_url` is deprecated: it still applies to the main provider for
one release, and a saved value is copied to that server's own setting on the
first start.

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
