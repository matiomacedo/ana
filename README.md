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

> **Status:** the latest release is v0.2.0. The source lives in a private
> repository; this one hosts the documentation, issue tracker, and
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

- **Write and edit code** — file, multi-edit, symbol, and LSP-aware editing
  tools, with post-edit syntax → lint → test verification feeding failures
  back to the model, and a check that re-runs the tests before a turn ends
- **Plan before acting** — a read-only `plan` permission mode researches the
  codebase and writes a reviewable plan before a single file changes
- **Human-in-the-loop safety** — destructive actions pause with a diff
  preview until you approve; allow/deny/ask permission rules apply in every
  mode
- **Sandboxed execution** — shell commands and test runs use `sandbox-exec` on
  macOS, or Docker or bubblewrap when available. Windows has no sandbox
- **Project memory** — `ana.md` instructions, a semantic code index and durable
  per-project "lessons" carry across sessions
- **Undo anything** — per-file snapshots, single-file `undo`, and full
  session `/rewind` that restores conversation and workspace together
- **Extensible** — MCP servers, lifecycle-hook plugins, markdown skills,
  custom slash commands, and shell hooks
- **Background review** — `ana watch` reviews your diffs as you save;
  `ana agents` runs long tasks in the background

## What's new in v0.2.0

- **Safer by default:** shell commands and test runs use `sandbox-exec` on macOS, and a
  cloned project's hooks, plugins and MCP servers stay off until you run `ana trust`
- **Checks before it finishes:** Ana re-runs the tests for the files it edited before a
  turn ends, and says plainly if any still fail
- **Faster start:** titles and `ana.md` generation wait until your first turn finishes,
  and the automatic context window is now 32K, which uses much less memory
- **A clearer terminal:** one-line tool steps, approvals that show what will run, and
  error messages that say how to fix the problem. Esc now interrupts a turn

See the [full release notes](https://github.com/matiomacedo/ana/releases/tag/v0.2.0).

## How it works

```
ana CLI (Typer + Rich)
   │  REST + WebSocket, bearer token
FastAPI backend (localhost:8765)
   │
LangGraph agent   safety → memory → reason → act → observe → memory ⟲
   │              reason → finish check → done
   │
Message window, session summaries, semantic code index (LanceDB, SQLite)
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
| [Tools](https://matiomacedo.github.io/ana/features/tools/) | All 30 built-in tools |
| [Memory](https://matiomacedo.github.io/ana/features/memory/) | The message window, summaries, code index, lessons |
| [Security model](https://matiomacedo.github.io/ana/reference/security/) | Project trust, sandbox, secrets redaction, and what isn't protected |
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
