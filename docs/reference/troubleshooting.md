# Troubleshooting

Start with the built-in diagnostics — it checks the Ollama binary, the
backend, the embedding model, the port, the session token, and the runtime
directories in one pass:

```bash
ana doctor
```

## Backend won't start or is unreachable

**"Cannot connect to backend" / "Ana backend is not running"**

- `ana`, `ana chat`, and `ana print` auto-start the backend; other
  commands require one to be running (`ana serve`).
- Check the auto-started backend's log: `~/.ana/daemon/backend.log`.
- Check the port isn't taken by something else: `lsof -i :8765`
  (macOS/Linux). Change it with `ANA_API_PORT`.

**"Authentication failed. The backend token may have changed."**

The CLI reads the bearer token from `~/.ana/session.token`. A stale token
usually means the backend was restarted by a different user or `ANA_HOME`
points somewhere unexpected. Stop the backend, delete the token file, and
start it again — it regenerates the token on startup.

**WebSocket closed with code 4001**

Same cause: the token the CLI sent doesn't match the backend's. Fix as
above.

## Ollama problems

**"Ollama binary not found" / connection refused on port 11434**

Install Ollama from [ollama.com](https://ollama.com/download) and confirm
it's running:

```bash
curl http://localhost:11434/api/tags   # expect {"models":[...]}
```

If Ollama runs elsewhere, set `OLLAMA_HOST` in `.env`.

**"default_model_not_installed" warning at startup**

Your configured `default_model` (env, settings file, or saved selection)
isn't pulled. Either `ollama pull <model>` or unset it to let Ana
auto-select a model that fits your RAM/VRAM.

**Memory features are silent / recall never finds anything**

The memory system needs the embedding model:

```bash
ollama pull qwen3-embedding:0.6b
```

**First response takes minutes**

That's the model cold-loading into RAM/VRAM — the status line shows
"Waiting for model…". Subsequent turns are fast while the model stays
loaded (`ANA_OLLAMA_KEEP_ALIVE`, default 30m). If every turn is slow, the
model is likely too big for your hardware — see the
[model recommendations](../index.md#model-recommendations).

**Responses derail or loop in long sessions**

Local models degrade in long contexts. Try `/compact` to summarise the
conversation, or a stronger model with `/model`. The sampler defaults
(`ANA_MIN_P`, `ANA_REPEAT_PENALTY`) already guard against loops — raising
`repeat_penalty` above ~1.1 hurts code output.

**The model forgets things sooner than its context should allow**

Check what Ana actually loaded the model with:

```bash
ana models info <model>   # Allocated: … tokens · … for the prompt
ana doctor                # "Context allocation" — the window and what chose it
```

The `Allocated` line is the real window; `/context` is a budget inside it. If
it's smaller than you expect, something above the auto value is setting it —
`ANA_OLLAMA_NUM_CTX`, the `context_length` setting, or `OLLAMA_CONTEXT_LENGTH`
— and `ana models info` names which. See
[Context window](../configuration/models.md#context-window).

**Ollama's context slider doesn't seem to apply**

Ana sends an explicit `num_ctx` with every request, which overrides the
server's default. It honours `OLLAMA_CONTEXT_LENGTH`, but only when
`ANA_OLLAMA_NUM_CTX` and the `context_length` setting are both unset —
`ana doctor` warns when your server setting is being shadowed.

## Agent behaviour

**"Graph already running for this session" (status `busy`)**

A turn is still in flight. Wait for it, or interrupt it with ++esc++ in chat.

**HTTP 429 on /message**

The backend rate-limits messages to 10/minute per client by default. Raise
it with `ANA_MESSAGE_RATE_LIMIT_PER_MINUTE`.

**"Tool 'X' is not permitted in plan mode"**

Plan mode is read-only by design. Switch modes with `/mode default` (or
`/plan execute` to act on a finished plan). See
[Permission modes](../configuration/permissions.md).

**"Permission denied: <action> on <target>"**

A deny rule in your permission store matched. Inspect and edit with
`ana permissions list` / `ana permissions remove <rule-id>`.

**Files Ana refuses to touch**

The [path-safety layer](security.md#path-safety) jails all file tools to
the session's project directory and blocks sensitive prefixes (`~/.ssh`,
`/etc/`, `~/.ana/`, …) and `.anaignore` matches. This is by design; run
Ana with the right `--project` directory instead of trying to reach
outside it.

## Shell & sandbox

**"shell commands run unsandboxed" on macOS/Windows**

Without Docker installed, `ANA_SANDBOX_MODE=auto` falls back to local
(unsandboxed) execution. Install Docker for container isolation, or set
`ANA_SANDBOX_MODE=docker` to fail loudly instead of falling back.

**Shell commands time out**

The per-execution limit is `ANA_SANDBOX_TIMEOUT_SECS` (default 30). Raise
it for slow test suites.

## Resetting state

| What | How |
|---|---|
| One session | `ana session delete <id>` |
| Conversation context | `/clear` in chat, or `/rewind` |
| Archival memory | `ana memory prune --policy session_end --yes` |
| Everything (nuclear) | Stop the backend, `rm -rf ~/.ana/` |

Deleting `~/.ana/` removes the token, all sessions, checkpoints, memory,
skills, plugins, and settings. It is regenerated with defaults on the next
start.

## Still stuck?

- Run `ana doctor` and include its output in your report.
- Backend logs: `~/.ana/daemon/backend.log`. Set `ANA_LOG_LEVEL=DEBUG` for
  more detail.
- Open an issue with the failing command, the log excerpt, your OS, and
  your model. For security issues, use private vulnerability reporting
  instead of a public issue.
