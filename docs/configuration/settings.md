# Settings & environment variables

Ana reads configuration from three places, with a strict precedence:

```
environment variable  >  settings file  >  built-in default
```

- **Environment variables** (`.env` in the project, or your shell) always
  win. All variables have working defaults — a fresh install needs none.
- **`~/.ana/settings.json`** — backend settings, edited via `/settings` in
  chat or the `GET`/`PATCH /settings` API. A `PATCH` that changes
  `embedding_provider` or `embedding_model` while lessons or code-index
  vectors are saved answers `409` with `{"code": "embedding_reset_required",
  "lessons": N, "chunks": N}` and saves nothing; send it again with
  `"confirm": true` to delete them and switch (see
  [Embeddings](models.md#embeddings)).
- **`~/.ana/cli_config.toml`** — CLI-side preferences, created with
  defaults on the first `ana` run.

## The `/settings` page

`/settings` inside `ana chat` opens a full-screen settings editor covering
both CLI options and backend settings: ++up++/++down++ moves between
entries, ++left++/++right++ (or ++space++) cycles enum and boolean values
in place, ++enter++ edits free-form values inline, and closing the page
(++q++ or ++esc++) saves everything you changed — ++ctrl+c++ discards.
Env-locked settings are shown but not editable.

The page opens on the **Provider** group: each [model role](models.md#model-roles)'s
provider and model, and the key or address each provider in use needs (a
cloud provider's `<id>_api_key`, a local server's `<id>_base_url` and
`backend_api_key`). Then come the CLI and the other backend settings. The keys of the providers you aren't using are
folded under **Other provider keys**; press ++o++ to show or hide them.
A key is typed hidden and never shown back, only as `set …1234`.

The Mac app's **Settings → Provider** works the same way: a provider and a
model menu for each role, the key or address of each provider in use, and a
line saying whether each role's provider answers.

```bash
# Non-interactive / scripted:
#   /settings verify_level lint          (backend)
#   /settings backend anthropic          (switches now; prints models + key check)
#   /settings anthropic_api_key sk-ant-...
#   /settings cli:show_context_budget false
cat ~/.ana/cli_config.toml
cat ~/.ana/settings.json
```

## Environment variables

### Ollama & models

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint, when `ANA_OLLAMA_BASE_URL` is unset |
| `OLLAMA_DEFAULT_MODEL` | *(auto)* | Chat model. Unset: picked by RAM/VRAM — see [model recommendations](../index.md#model-recommendations) |
| `ANA_EMBED_MODEL` | *(the provider's)* | Embedding model (`embedding_model`); `OLLAMA_EMBED_MODEL` also works on Ollama. Unset: `qwen3-embedding:0.6b` on Ollama, the provider's default elsewhere — see [Embeddings](models.md#embeddings) |
| `ANA_OLLAMA_NUM_CTX` | *(auto)* | Context window to load the model with (Ollama's `num_ctx`). Unset: 32K, or less when the model's trained limit or your memory is smaller. `0` sends no `num_ctx` at all. Same value as the `context_length` setting below — see [Context window](models.md#context-window) |
| `OLLAMA_CONTEXT_LENGTH` | — | Ollama's own server-side setting. Ana honours it when neither `ANA_OLLAMA_NUM_CTX` nor `context_length` is set |
| `ANA_OLLAMA_KEEP_ALIVE` | `30m` | How long the chat model stays loaded between turns |
| `ANA_EMBED_KEEP_ALIVE` | `2m` | How long the embedding model stays loaded after a batch — kept short so it unloads instead of evicting the chat model's KV cache |
| `ANA_BACKGROUND_KEEP_ALIVE` | `5m` | How long helper models (compaction, titles, lessons) stay loaded after a job |
| `ANA_BACKGROUND_MODEL` | *(auto)* | Helper (background) role: titles, compaction summaries, lesson distillation. Unset: the provider's `background: true` preset in the cloud; locally the session's own model when it runs there, else the smallest Ollama model — see [Model roles](models.md#model-roles) |
| `ANA_THINKING_EFFORT` | `default` | How hard models that can think do so: `default` \| `off` \| `low` \| `medium` \| `high`. `/effort` overrides it per session — see [Thinking effort](models.md#thinking-effort) |
| `ANA_ESCALATION_MODEL` | *(auto)* | Escalation role: format-repair retries and auto-escalate. Unset: on Ollama the largest installed model that fits; elsewhere none |
| `ANA_SUBAGENT_MODEL` | *(auto)* | Subagent role. Unset: the session's model when it runs on the subagent provider, else that provider's default |

### Provider

| Variable | Default | Meaning |
|---|---|---|
| `ANA_BACKEND` | `ollama` | The main provider: `ollama` \| `lmstudio` \| `llamacpp` \| `openai_compat` (vLLM and other OpenAI-compatible servers) \| `anthropic` \| `openai` \| `google` \| `openrouter` \| `groq` \| `deepseek` \| `xai` \| `mistral` \| `together` \| `fireworks` \| `cerebras`. Set from `/settings` or the Mac app it applies on the next message, no restart — see [Providers](models.md#providers) |
| `ANA_SUBAGENT_PROVIDER` | `ollama` | Provider of the subagent role (same choices) |
| `ANA_BACKGROUND_PROVIDER` | `ollama` | Provider of the helper role (same choices). The retired value `active` still means the main provider |
| `ANA_ESCALATION_PROVIDER` | `ollama` | Provider of the escalation role (same choices) |
| `ANA_EMBEDDING_PROVIDER` | `ollama` | Provider of embeddings: a local server, `openai` \| `google` \| `mistral` \| `fireworks` \| `openrouter`, or `off` — see [Embeddings](models.md#embeddings) |
| `ANA_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama's address (`ollama_base_url`); falls back to `OLLAMA_HOST` |
| `ANA_LMSTUDIO_BASE_URL` | `http://localhost:1234` | LM Studio's address (`lmstudio_base_url`); falls back to `LMSTUDIO_HOST` |
| `ANA_LLAMACPP_BASE_URL` | `http://localhost:8080` | llama.cpp's address (`llamacpp_base_url`); falls back to `LLAMACPP_HOST` |
| `ANA_OPENAI_COMPAT_BASE_URL` | `http://localhost:8000` | The OpenAI-compatible server's address (`openai_compat_base_url`); falls back to `OPENAI_COMPAT_HOST` |
| `ANA_BACKEND_BASE_URL` | — | Deprecated: the main provider's address when it is a local server and its own setting is unset. A saved value moves to that server's own setting on the next start |
| `ANA_BACKEND_API_KEY` | — | Bearer token for a local server (they usually ignore it); falls back to `OPENAI_COMPAT_API_KEY` |

Cloud provider keys, each also a setting named `<id>_api_key`
(`anthropic_api_key`, `google_api_key`…). The variable wins over the saved
setting:

| Variable | Provider |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic |
| `OPENAI_API_KEY` | OpenAI |
| `GEMINI_API_KEY`, then `GOOGLE_API_KEY` | Google Gemini |
| `OPENROUTER_API_KEY` | OpenRouter |
| `GROQ_API_KEY` | Groq |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `XAI_API_KEY` | xAI |
| `MISTRAL_API_KEY` | Mistral |
| `TOGETHER_API_KEY` | Together AI |
| `FIREWORKS_API_KEY` | Fireworks |
| `CEREBRAS_API_KEY` | Cerebras |

### Agent behaviour

| Variable | Default | Meaning |
|---|---|---|
| `ANA_CODE_RAG` | `off` | Add semantic code search results to every turn. The `code_search` tool and the repo map work either way |
| `ANA_CODE_INDEX_REFRESH_INTERVAL_S` | `120` | Minimum seconds between background code-index refreshes (0 = every turn) |
| `ANA_VERIFY_LEVEL` | `test` | Post-edit verification depth: `off` \| `syntax` \| `lint` \| `test` — see [Verification](../features/verification.md) |
| `ANA_AUTO_ESCALATE` | `on` | Escalate to a larger installed model when post-edit verification failures stop shrinking. See [Auto-escalation](../features/verification.md#auto-escalation) |
| `ANA_SLEEP_TIME` | `off` | Idle-time memory consolidation (experimental) — see [Memory](../features/memory.md#sleep-time-consolidation-experimental) |
| `ANA_CHECKPOINT_DURABILITY` | `sync` | `sync` writes a checkpoint per step and waits for it (mid-turn crash recovery); `async` doesn't wait; `exit` writes one per turn (fastest, loses a turn that crashes) |
| `ANA_RESEARCH_AGENT_TIMEOUT_SECS` | `120` | Timeout for `research` subagents |
| `ANA_CRITIC_AGENT_TIMEOUT_SECS` | `60` | Timeout for review subagents |
| `ANA_INIT_AGENT_TIMEOUT_SECS` | `60` | Timeout for the project-init agent (`/init`) |

### Decoding quality

Samplers applied to the main reasoning loop. Per-model overrides live in a
preset `sampling:` block ([Models & presets](models.md)); these env vars win
over both. The conservative defaults add a probability floor and a light,
code-appropriate repetition penalty — local models loop and derail in long
contexts without them.

| Variable | Default | Meaning |
|---|---|---|
| `ANA_MIN_P` | `0.05` | min-p probability floor (0 disables) |
| `ANA_REPEAT_PENALTY` | `1.05` | Keep low for code (1.0–1.05); Ollama's own 1.1 over-penalises |
| `ANA_TOP_P` | `0.95` | nucleus sampling |
| `ANA_TOP_K` | `40` | top-k sampling |
| `ANA_CONSTRAIN_MAIN_CALL` | `0` | Grammar-constrain the *first* generation (not just repair) so weak models emit a valid action first-try |
| `ANA_BEST_OF_N` | `1` | Verifier-selected best-of-N for file edits: sample N candidates, keep the one that parses. 1 disables |

### Backend

| Variable | Default | Meaning |
|---|---|---|
| `ANA_API_PORT` | `8765` | Backend HTTP port |
| `ANA_API_HOST` | `127.0.0.1` | Bind address — never expose to a network |
| `ANA_BACKEND_IDLE_TIMEOUT_S` | `120` | How long an auto-started backend waits after its last client leaves before it stops. A backend from `ana serve` or `ana daemon start` keeps running |
| `ANA_ENV` | `development` | `development` \| `production` |
| `ANA_HOME` | `~/.ana` | All runtime data (token, DBs, memory, skills, plugins, MCP config) |
| `ANA_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `ANA_MESSAGE_RATE_LIMIT_PER_MINUTE` | `10` | Message rate limit per remote client; loopback clients have none |

`GET /health` has a `roles` list: one entry per model role (`main`,
`subagent`, `background`, `escalation`, `embeddings`) with its `provider`,
`model`, whether it is `reachable`, and a `detail` naming the setting to
change when it isn't. Clients compare the `api` level from
`GET /health/ready`; per-role providers (roles in `/health`, `provider` on
sessions and models, the embedding `confirm`) arrived with level 8.

### Sandbox

| Variable | Default | Meaning |
|---|---|---|
| `ANA_SANDBOX_MODE` | `auto` | `auto` \| `sandbox-exec` \| `docker` \| `bubblewrap` \| `local` — see [Security](../reference/security.md#sandbox) |
| `ANA_SANDBOX_TIMEOUT_SECS` | `30` | Max seconds per code/shell execution |
| `ANA_SANDBOX_IMAGE` | `ana-sandbox:latest` | Docker image used when mode is docker/auto |

### Memory & web search

| Variable | Default | Meaning |
|---|---|---|
| `ANA_MEMORY_RETENTION` | `30_days` | How long compaction summaries are kept: `session_end` \| `1_day` \| `30_days` \| `1_year` \| `forever` |
| `ANA_SEARCH_PROVIDER` | `duckduckgo` | `duckduckgo` (no key) \| `tavily` \| `brave` |
| `TAVILY_API_KEY` | — | Required for `tavily` |
| `BRAVE_SEARCH_API_KEY` | — | Required for `brave` |

## CLI configuration (`~/.ana/cli_config.toml`)

```toml
default_mode         = "default"   # Permission mode for new sessions: plan|default|auto_accept
default_model        = ""          # Empty = use OLLAMA_DEFAULT_MODEL
api_host             = "127.0.0.1"
api_port             = 8765
show_context_budget  = true        # Show context gauge in status bar
retention_policy     = "30_days"   # Default for `ana memory prune`
vi_mode              = false       # Vim keybindings in the chat prompt (takes effect next chat)
notify_after_seconds = 60          # Terminal notification when a turn takes longer (0 = off)
```

## `.anaignore`

Placed at the project root. Patterns are fnmatch globs, and a directory name excludes
that directory at any depth. A `!` pattern re-includes a path, and the last matching
pattern wins. File tools and code search
won't read, index or write matching files, but `shell_command` doesn't read this file:

```gitignore
# Secrets
.env
*.pem
*.key
credentials.json

# Build artifacts (performance)
node_modules/
dist/
__pycache__/
*.pyc
```

There is no built-in default ignore list — patterns come entirely from your
`.anaignore`.

## Related

- [Models & presets](models.md) — providers, per-model profiles, presets and thinking effort
- [Permission modes](permissions.md) — session-level access control
