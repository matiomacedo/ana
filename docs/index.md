# Ana

**A fully local AI coding agent.** Ana runs entirely on your machine via
[Ollama](https://ollama.com) — no cloud APIs, no subscriptions, no code
leaving your laptop.

Ana understands your project, plans before it touches anything, writes and
verifies code, and remembers what it learned across sessions.

```bash
cd ~/your/project
ana
# ❯ Add input validation to the signup endpoint and run the tests
```

## What Ana can do

- **Write and edit code** — file, patch, multi-edit, and LSP-aware editing
  tools, with post-edit syntax → lint → test verification feeding failures
  back to the model so it self-corrects
- **Plan before acting** — a read-only `plan` permission mode researches the
  codebase and writes a reviewable plan before a single file changes
- **Human-in-the-loop safety** — destructive actions pause with a diff
  preview until you approve; allow/deny/ask permission rules apply in every
  mode
- **Sandboxed execution** — Python runs under RestrictedPython; shell
  commands run in Docker or Bubblewrap when available
- **Persistent memory** — a three-tier memory system, a semantic code index,
  and durable per-project "lessons" survive across sessions
- **Undo anything** — per-file snapshots, single-file `undo`, and full
  session `/rewind` that restores conversation and workspace together
- **Extensible** — MCP servers, lifecycle-hook plugins, markdown skills,
  custom slash commands, and shell hooks
- **Background review** — `ana watch` reviews your diffs as you save;
  `ana agents` runs long tasks in the background

## Get started

<div class="grid cards" markdown>

- **[Installation](getting-started/installation.md)**

    Prerequisites, install steps, and runtime directories

- **[Quickstart](getting-started/quickstart.md)**

    Your first session in five minutes

- **[CLI reference](usage/cli-reference.md)**

    Every command, flag, and slash command

- **[Troubleshooting](reference/troubleshooting.md)**

    Common problems and `ana doctor`

</div>

## Understand Ana

| Guide | What it covers |
|---|---|
| [Architecture](reference/architecture.md) | The layered stack, the agent graph, key design decisions |
| [Permission modes](configuration/permissions.md) | `plan` / `default` / `auto_accept` and permission rules |
| [Tools](features/tools.md) | All 34 built-in tools and how they're gated |
| [Memory](features/memory.md) | Three memory tiers, the code index, lessons, retention |
| [Verification](features/verification.md) | Deterministic post-edit checks instead of an LLM critic |
| [Security](reference/security.md) | Constitution, sandbox, secrets redaction, path safety |

## Extend Ana

| Guide | What it covers |
|---|---|
| [MCP servers](extend/mcp.md) | Connect external tools via the Model Context Protocol |
| [Plugins](extend/plugins.md) | Lifecycle-hook plugins |
| [Skills](extend/skills.md) | Markdown skills, user-authored and auto-crystallized |
| [Hooks & custom commands](extend/hooks.md) | Shell hooks around tool calls, your own slash commands |

## How it works

```
ana CLI (Typer + Rich)
   │  REST + WebSocket, bearer token
FastAPI backend (localhost:8765)
   │
LangGraph agent   safety → memory → reason → act → observe → memory ⟲
   │
3-tier memory + semantic code index (LanceDB, SQLite, git snapshots)
   │
Ollama (local inference, native tool calling)
```

Read the full [architecture overview](reference/architecture.md).

## Model recommendations

Ana picks a default automatically when `OLLAMA_DEFAULT_MODEL` is unset. The
budget is the discrete GPU's VRAM when an NVIDIA/AMD card is detected (that's
what limits GPU offload), otherwise total system RAM (Apple unified memory or
a CPU-only box). Model weights are budgeted at roughly 60% of that so the KV
cache, your context, the background model, and the OS still fit — a model
that barely fits runs slower than a smaller one with headroom.

| Your RAM / VRAM | Recommended model | Pull command |
|----------|------------------|--------------|
| 8 GB | qwen3.5:4b | `ollama pull qwen3.5:4b` |
| 16 GB | qwen3.5:9b | `ollama pull qwen3.5:9b` |
| 24 GB | devstral-small-2:24b | `ollama pull devstral-small-2:24b` |
| 32 GB+ | qwen3.6:27b | `ollama pull qwen3.6:27b` |

## Security

Ana executes code and shell commands on your machine — read the
[security model](reference/security.md) before pointing it at anything
sensitive.
