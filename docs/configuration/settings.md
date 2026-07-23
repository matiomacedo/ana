# Settings & environment variables

Ana reads configuration from three places, with a strict precedence:

```
environment variable  >  settings file  >  built-in default
```

- **Environment variables** (`.env` in the project, or your shell) always
  win. All variables have working defaults — a fresh install needs none.
- **`~/.ana/settings.json`** — backend settings, edited via `/settings` in
  chat or the `GET`/`PATCH /settings` API.
- **`~/.ana/cli_config.toml`** — CLI-side preferences, created with
  defaults on the first `ana` run.

## The `/settings` page

`/settings` inside `ana chat` opens a full-screen settings editor covering
both CLI options and backend settings: ++up++/++down++ moves between
entries, ++left++/++right++ (or ++space++) cycles enum and boolean values
in place, ++enter++ edits free-form values inline, and closing the page
(++q++ or ++esc++) saves everything you changed — ++ctrl+c++ discards.
Env-locked settings are shown but not editable.

```bash
# Non-interactive / scripted:
#   /settings verify_level lint          (backend)
#   /settings cli:show_context_budget false
cat ~/.ana/cli_config.toml
cat ~/.ana/settings.json
```

## Environment variables

### Ollama & models

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_DEFAULT_MODEL` | *(auto)* | Chat model. Unset: picked by RAM/VRAM — see [model recommendations](../index.md#model-recommendations) |
| `OLLAMA_EMBED_MODEL` | `qwen3-embedding:0.6b` | Embedding model for the memory system |
| `ANA_OLLAMA_NUM_CTX` | *(auto)* | Context window to load the model with (Ollama's `num_ctx`). Unset: the model's trained limit, capped to what your memory can hold as KV cache. `0` sends no `num_ctx` at all. Same value as the `context_length` setting below — see [Context window](models.md#context-window) |
| `OLLAMA_CONTEXT_LENGTH` | — | Ollama's own server-side setting. Ana honours it when neither `ANA_OLLAMA_NUM_CTX` nor `context_length` is set |
| `ANA_OLLAMA_KEEP_ALIVE` | `30m` | How long the chat model stays loaded between turns |
| `ANA_EMBED_KEEP_ALIVE` | `2m` | How long the embedding model stays loaded after a batch — kept short so it unloads instead of evicting the chat model's KV cache |
| `ANA_BACKGROUND_KEEP_ALIVE` | `5m` | How long helper models (compaction, titles, lessons) stay loaded after a job |
| `ANA_BACKGROUND_MODEL` | *(auto)* | Background role: compaction summaries + lesson distillation. Defaults to the smallest installed chat model ≥ 4B params |
| `ANA_ESCALATION_MODEL` | *(auto)* | Escalation role: format-repair retries and auto-escalate. Defaults to the largest installed |

### Inference backend

| Variable | Default | Meaning |
|---|---|---|
| `ANA_BACKEND` | `ollama` | `ollama` \| `lmstudio` \| `llamacpp` \| `openai_compat` (covers vLLM and other OpenAI-compatible servers). Requires a backend restart |
| `ANA_BACKEND_BASE_URL` | *(per-backend default)* | Base URL of the inference server |
| `ANA_BACKEND_API_KEY` | — | Bearer token for the backend (local servers usually ignore it) |

### Agent behaviour

| Variable | Default | Meaning |
|---|---|---|
| `ANA_CODE_RAG` | `on` | Semantic code retrieval into the RAG context tier (the repo map is always on) |
| `ANA_CODE_INDEX_REFRESH_INTERVAL_S` | `120` | Minimum seconds between background code-index refreshes (0 = every turn) |
| `ANA_VERIFY_LEVEL` | `test` | Post-edit verification depth: `off` \| `syntax` \| `lint` \| `test` — see [Verification](../features/verification.md) |
| `ANA_AUTO_ESCALATE` | `on` | Escalate to a larger installed model after 2 consecutive post-edit verification failures in one turn |
| `ANA_SLEEP_TIME` | `off` | Idle-time memory consolidation (experimental) — see [Memory](../features/memory.md#sleep-time-consolidation-experimental) |
| `ANA_CHECKPOINT_DURABILITY` | `exit` | `exit` writes one full-state checkpoint per turn; `async` restores per-step checkpoints (mid-turn crash recovery, slower) |
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
| `ANA_RRF_K` | `60` | Reciprocal Rank Fusion constant for Tier-2 (BM25+vector) recall; higher flattens top-rank weights |
| `ANA_BEST_OF_N` | `1` | Verifier-selected best-of-N for file edits: sample N candidates, keep the one that parses. 1 disables |

### Backend

| Variable | Default | Meaning |
|---|---|---|
| `ANA_API_PORT` | `8765` | Backend HTTP port |
| `ANA_API_HOST` | `127.0.0.1` | Bind address — never expose to a network |
| `ANA_ENV` | `development` | `development` \| `production` |
| `ANA_HOME` | `~/.ana` | All runtime data (token, DBs, memory, skills, plugins, MCP config) |
| `ANA_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `ANA_MESSAGE_RATE_LIMIT_PER_MINUTE` | `10` | Message rate limit per client |

### Sandbox

| Variable | Default | Meaning |
|---|---|---|
| `ANA_SANDBOX_MODE` | `auto` | `auto` \| `docker` \| `bubblewrap` \| `local` — see [Security](../reference/security.md#sandbox) |
| `ANA_SANDBOX_TIMEOUT_SECS` | `30` | Max seconds per code/shell execution |
| `ANA_SANDBOX_IMAGE` | `ana-sandbox:latest` | Docker image used when mode is docker/auto |

### Memory & web search

| Variable | Default | Meaning |
|---|---|---|
| `ANA_MEMORY_RETENTION` | `30_days` | `session_end` \| `1_day` \| `30_days` \| `1_year` \| `forever` |
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
show_reflections     = false       # Show reflection events in chat
retention_policy     = "30_days"   # Default for `ana memory prune`
vi_mode              = false       # Vim keybindings in the chat prompt (takes effect next chat)
notify_after_seconds = 60          # Terminal notification when a turn takes longer (0 = off)
```

## `.anaignore`

Placed at the project root or anywhere in the directory tree, using
gitignore syntax. Files matching these patterns are never read, listed,
indexed, or written by Ana:

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

- [Models & presets](models.md) — per-model profiles and sampling overrides
- [Permission modes](permissions.md) — session-level access control
