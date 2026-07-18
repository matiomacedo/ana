# Quickstart

Get from a fresh install to a working session in five minutes.

!!! note "Distribution coming soon"
    Ana is not yet publicly distributed — see
    [Installation](installation.md) for status.

## 1. Pull a model

Ana needs a chat model and an embedding model (for the memory system):

```bash
ollama pull qwen3.5:9b            # 16 GB RAM — recommended starting model
ollama pull qwen3-embedding:0.6b  # required for the memory system
```

Smaller or larger machine? See the
[model recommendations](../index.md#model-recommendations) — Ana also
auto-selects a model that fits your RAM/VRAM if you skip this step and
pull nothing explicitly.

## 2. Start chatting

```bash
cd ~/some/project
ana
```

That's it — `ana` starts (and stops) the backend for you and drops into an
interactive chat scoped to the current directory. Type a message and press
Enter:

```
❯ Explain how authentication works in this project
❯ Add input validation to the signup endpoint and run the tests
```

## 3. Try the essentials

**Plan before touching anything.** `plan` mode is read-only — the agent
researches your codebase and writes a reviewable plan instead of editing:

```bash
ana chat --mode plan
# ❯ Plan how to migrate this Flask app to FastAPI
```

or type `/plan` inside a running chat, then `/plan execute` to act on the
finished plan. See [Permission modes](../configuration/permissions.md).

**Approve changes as they happen.** In the default mode, destructive actions
(file writes, shell commands) pause with a diff preview until you approve.
Choose "always allow" for a tool to stop being asked for the rest of the
session, or switch to `/mode auto_accept` when you trust the plan.

**One-shot, scriptable runs.** `ana print` sends a single prompt and prints
the reply — no interactive session:

```bash
ana print "explain the auth flow"
git diff | ana print -               # prompt from stdin
ana print -f json "…"                # full transcript as JSON
```

See [Headless mode](../usage/headless.md).

**Check your setup.** If anything misbehaves:

```bash
ana doctor     # one-pass diagnostics: Python, Ollama, models, ports, token
ana health     # backend + Ollama status
```

## 4. Useful in-chat commands

| Command | What it does |
|---|---|
| `/mode plan` | Switch to read-only research mode |
| `/model` | Switch model (picker) |
| `/rewind` | Roll back the last turn — conversation *and* files |
| `/compact` | Summarise the conversation to free context |
| `/context` | Show the context budget breakdown |
| `/help` | Everything else |

Full list: [Interactive mode](../usage/interactive-mode.md).

## Next steps

- [CLI reference](../usage/cli-reference.md) — every command and flag
- [Configuration](../configuration/settings.md) — env vars, config files
- [Permission modes](../configuration/permissions.md) — how much Ana may touch
- [Memory](../features/memory.md) — what Ana remembers between sessions
