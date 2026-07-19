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

**[📖 Documentation](https://matiomacedo.github.io/ana/)** · [Report an issue](https://github.com/matiomacedo/ana/issues)

> **Status:** Ana is in final benchmarking ahead of its first public
> release. This repository hosts the documentation, issue tracker, and
> [binary releases](https://github.com/matiomacedo/ana/releases).

## Install

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/matiomacedo/ana/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/matiomacedo/ana/main/install.ps1 | iex
```

Requires [Ollama](https://ollama.com). Full details:
[Installation](https://matiomacedo.github.io/ana/getting-started/installation/).

## Highlights

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

Runs natively on macOS, Linux, and Windows. Read the full
[architecture overview](https://matiomacedo.github.io/ana/reference/architecture/).

## Model recommendations

Ana picks a default automatically based on your RAM/VRAM:

| Your RAM / VRAM | Recommended model |
|----------|------------------|
| 8 GB | qwen3.5:4b |
| 16 GB | qwen3.5:9b |
| 24 GB | devstral-small-2:24b |
| 32 GB+ | qwen3.6:27b |

## Documentation

| Guide | What it covers |
|---|---|
| [Quickstart](https://matiomacedo.github.io/ana/getting-started/quickstart/) | Your first session in five minutes |
| [CLI reference](https://matiomacedo.github.io/ana/usage/cli-reference/) | Every command, flag, and slash command |
| [Permission modes](https://matiomacedo.github.io/ana/configuration/permissions/) | plan / default / auto_accept + permission rules |
| [Tools](https://matiomacedo.github.io/ana/features/tools/) | All 32 built-in tools |
| [Memory](https://matiomacedo.github.io/ana/features/memory/) | The three tiers, code index, lessons |
| [Security model](https://matiomacedo.github.io/ana/reference/security/) | Constitution, sandbox, secrets redaction, path safety |
| [Troubleshooting](https://matiomacedo.github.io/ana/reference/troubleshooting/) | Common problems and `ana doctor` |

## Security

Ana executes code and shell commands on your machine — read the
[security model](https://matiomacedo.github.io/ana/reference/security/)
before pointing it at anything sensitive. To report a vulnerability, use
GitHub's private vulnerability reporting on this repository rather than a
public issue.

## License

The documentation in this repository is licensed under
[CC BY 4.0](LICENSE).
