# Installation

!!! note "Distribution coming soon"
    Ana is not yet publicly distributed — a packaged release is planned
    after the current benchmarking round. This page documents the
    installation flow so you know what to expect. Watch this repository
    for the release announcement.

## Prerequisites

| Requirement | Notes |
|---|---|
| macOS, Linux, or Windows 10+ | Native on all three |
| Python 3.11+ | Managed automatically by `uv` |
| [Ollama](https://ollama.com) | Installed and running |
| 8 GB RAM minimum | 16 GB recommended for mid-tier models |

### uv

Ana uses [`uv`](https://docs.astral.sh/uv/) to manage Python versions and
dependencies — it downloads the correct Python for you.

```bash
# macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Ollama

Download and install Ollama from [ollama.com](https://ollama.com/download),
then verify it is running:

```bash
curl http://localhost:11434/api/tags
# Expected: {"models":[...]}
```

## Installing Ana

Once you have the Ana source, `make dev-setup` performs the full setup:

```bash
cd ana
make dev-setup
```

This creates a Python virtual environment via uv, installs all dependencies,
and sets up the development hooks.

### Verify the installation

```bash
uv run ana --help
# Expected: help tree with chat, session, memory, skills, models, health, ...

ana doctor
# One-pass diagnostics: Python, uv, Ollama, models, ports, token, directories
```

## Installing `ana` globally

To run `ana` from any directory like a system command (instead of
`uv run ana` inside the repo):

```bash
make install      # uv tool install
```

This builds Ana into an isolated environment and puts the `ana` executable
on your PATH (`~/.local/bin/ana`). After that, from any project directory:

```bash
cd ~/some/project
ana               # auto-starts the backend, then drops into chat
```

When you run `ana`, `ana chat`, or `ana print`, the CLI starts the backend
automatically if nothing is already listening on `127.0.0.1:8765`, waits for
it to become ready, and stops it again when the command exits (logs go to
`~/.ana/daemon/backend.log`). If a backend is already running it is reused
and left alone. Ollama must be running — `ana` prints a warning if it can't
reach it.

Optionally enable shell completion:

```bash
ana --install-completion
```

Remove the global install with `make uninstall`.

## Platform notes

=== "macOS"

    No additional steps. Ollama runs as a menubar app.

=== "Linux"

    Ollama runs as a systemd service after installation:

    ```bash
    systemctl --user status ollama
    ```

    Shell sandboxing can use Bubblewrap (`bwrap`) in addition to Docker —
    see [Security](../reference/security.md#sandbox).

=== "Windows"

    Ana runs natively on Windows. The `Makefile` targets are POSIX-only, so
    use the underlying `uv` commands directly:

    ```powershell
    uv sync                                       # instead of `make dev-setup`
    uv run uvicorn ana.api.main:app --port 8765   # instead of `make dev-backend`
    ```

    `uv sync` pulls the Windows-only dependencies (`pywin32`, `pywinpty`)
    automatically. The shell tools accept native commands (`dir`, `type`,
    `findstr`, `where`, …) run via `cmd /c`. Token-file permissions use
    Windows ACLs automatically — no manual steps needed.

## Runtime directories

Ana creates these directories on first run:

```
~/.ana/
├── session.token      ← Bearer token (auto-generated, chmod 600 / ACL)
├── sessions.db        ← SQLite: session metadata
├── checkpoints/
│   └── checkpoints.db ← SQLite: agent-graph checkpoints (resumable sessions)
├── permissions.db     ← SQLite: allow/deny/ask permission rules
├── lancedb/           ← LanceDB: archival memory, code index, lessons
├── memory/            ← Git repos: per-session compaction history
│   └── {session-id}/
├── skills/            ← Approved skill markdown files
├── plugins/           ← Installed plugins (trusted code — see Security)
├── mcp.json           ← Configured MCP servers
├── daemon/
│   ├── state.json     ← Background-agent state
│   ├── daemon.pid
│   └── backend.log
├── presets/           ← User overrides for model presets
└── cli_config.toml    ← CLI preferences
```

These directories persist across restarts. Relocate everything with the
`ANA_HOME` environment variable.

## Updating

```bash
git pull
uv sync          # update Python deps
make dev-setup   # re-run full setup (safe to run repeatedly)
```

## Uninstalling

```bash
make uninstall       # remove the global `ana` command
rm -rf ~/.ana/       # remove all Ana runtime data
```

Deleting `~/.ana/` removes the token, all sessions, checkpoints, memory,
skills, plugins, and settings. It is regenerated with defaults on the next
start.

## Next steps

- [Quickstart](quickstart.md) — your first session
- [Configuration](../configuration/settings.md) — environment variables and
  config files
