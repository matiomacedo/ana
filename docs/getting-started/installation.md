# Installation

Ana ships as a self-contained binary for macOS (Apple silicon), Linux
(x64), and Windows (x64) — no Python setup required. The only external
dependency is [Ollama](https://ollama.com).

!!! note "First release"
    Binaries are published on the [releases
    page](https://github.com/matiomacedo/ana/releases). If the install
    command reports no published release, the first public release hasn't
    landed yet — watch the repository for the announcement.

## Prerequisites

| Requirement | Notes |
|---|---|
| macOS (Apple silicon), Linux x64, or Windows 10+ x64 | Prebuilt binaries |
| [Ollama](https://ollama.com) | Installed and running |
| 8 GB RAM minimum | 16 GB recommended for mid-tier models |

Install Ollama from [ollama.com](https://ollama.com/download), then verify
it is running:

```bash
curl http://localhost:11434/api/tags
# Expected: {"models":[...]}
```

## Install Ana

=== "macOS / Linux"

    ```bash
    curl -fsSL https://raw.githubusercontent.com/matiomacedo/ana/main/install.sh | sh
    ```

    This downloads the latest release to `~/.local/share/ana` and puts an
    `ana` command in `~/.local/bin`. If `~/.local/bin` isn't on your PATH,
    the installer prints the line to add to your shell profile.

=== "Windows"

    ```powershell
    irm https://raw.githubusercontent.com/matiomacedo/ana/main/install.ps1 | iex
    ```

    This installs to `%LOCALAPPDATA%\Programs\ana` and adds it to your
    user PATH (restart the terminal afterwards).

=== "Manual download"

    Grab the archive for your platform from the
    [releases page](https://github.com/matiomacedo/ana/releases), verify it
    against `ana-<version>-checksums.txt`, extract it anywhere, and run the
    `ana` launcher inside. On macOS, if you downloaded through a browser
    and Gatekeeper objects, clear the quarantine flag:

    ```bash
    xattr -dr com.apple.quarantine path/to/ana
    ```

### Verify the installation

```bash
ana --help
ana doctor    # one-pass diagnostics: Ollama, models, ports, token, directories
```

## First run

```bash
cd ~/some/project
ana            # auto-starts the backend, drops into chat
```

When you run `ana`, `ana chat`, or `ana print`, the CLI starts the backend
automatically if nothing is already listening on `127.0.0.1:8765`, waits
for it to become ready, and stops it again when the command exits (logs go
to `~/.ana/daemon/backend.log`). If a backend is already running it is
reused and left alone. Ollama must be running — `ana` prints a warning if
it can't reach it.

Optionally enable shell completion:

```bash
ana --install-completion
```

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

Re-run the install command — it replaces the binary in place and leaves
your `~/.ana/` data untouched.

## Uninstalling

=== "macOS / Linux"

    ```bash
    rm -rf ~/.local/share/ana ~/.local/bin/ana   # the binary
    rm -rf ~/.ana/                               # all Ana runtime data
    ```

=== "Windows"

    ```powershell
    Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\ana"   # the binary
    Remove-Item -Recurse -Force "$env:USERPROFILE\.ana"            # runtime data
    ```

Deleting `~/.ana/` removes the token, all sessions, checkpoints, memory,
skills, plugins, and settings. It is regenerated with defaults on the next
start.

## Next steps

- [Quickstart](quickstart.md) — your first session
- [Configuration](../configuration/settings.md) — environment variables and
  config files
