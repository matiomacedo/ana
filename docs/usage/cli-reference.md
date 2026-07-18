# CLI reference

The `ana` command is the single entry point. `ana`, `ana chat`, and
`ana print` auto-start the backend if nothing is listening on
`127.0.0.1:8765`, and stop it again on exit. Other commands require a
running backend. Ollama must already be running.

## Chat

```bash
ana                       # interactive chat in "default" permission mode
ana chat                  # same
ana chat --mode plan --project ~/myproject
```

| Flag | Meaning |
|---|---|
| `--mode plan\|default\|auto_accept` | Permission mode for the session |
| `--project PATH` | Project directory the session is scoped to (default: cwd) |

In-chat slash commands are documented in
[Interactive mode](interactive-mode.md).

## Headless

```bash
ana print "explain this function"    # send one prompt, print the reply
ana print -f json "…"                # full transcript as JSON
ana print -f stream-json "…"         # one JSON event per line
git diff | ana print -               # prompt from stdin
ana print -s <session-id> "…"        # continue an existing session
```

`ana print` exits non-zero when the turn ends in a non-recoverable error.
See [Headless mode](headless.md) for scripting patterns.

## Diagnostics

```bash
ana doctor    # local toolchain diagnostics (Python, uv, Ollama, ports, token, …)
ana health    # backend and Ollama status
```

## Sessions

```bash
ana session list
ana session new --mode plan --project ~/myproject
ana session resume a3f1                # ID prefix works
ana session delete a3f1bc7d-...
```

See [Sessions & rewind](sessions.md).

## Memory

```bash
ana memory stats                                     # per-session archival counts + DB size
ana memory prune --policy 30_days --yes              # apply a retention policy
ana memory prune --policy session_end --session a3f1bc7d
```

Valid retention policies: `session_end`, `1_day`, `30_days`, `1_year`,
`forever`. See [Memory](../features/memory.md#retention-policies).

## Models

```bash
ana models list             # all available Ollama models with profiles
ana models info qwen3.5:9b  # full profile for one model
```

See [Models & presets](../configuration/models.md).

## Permissions

```bash
ana permissions list
ana permissions add edit "*.env" ask --desc "Confirm edits to env files"
ana permissions add bash "docker *" allow --desc "Allow docker commands"
ana permissions remove <rule-id>
ana permissions clear
ana permissions seed        # re-seed the built-in default rules
```

See [Permission modes](../configuration/permissions.md#permission-rules-allowdenyask).

## Skills

```bash
ana skills list             # crystallized skills awaiting approval
ana skills approve abc12345 # approve — materialises it under ~/.ana/skills/
ana skills reject abc12345
ana skills export / import
```

See [Skills](../extend/skills.md).

## MCP

```bash
ana mcp list      # configured servers (~/.ana/mcp.json)
ana mcp add ...
ana mcp remove ...
ana mcp status    # connection status; restart the backend after config changes
```

See [MCP servers](../extend/mcp.md).

## Plugins

```bash
ana plugin list
ana plugin install <repo-url>   # not sandboxed — trusted code only
ana plugin enable|disable <name>
ana plugin remove <name>
```

See [Plugins](../extend/plugins.md).

## Background agents

```bash
ana agents run "description of the task"   # start a background agent
ana agents list                            # list running/finished agents
ana agents logs <id>                       # tail its events
```

See [Subagents & background agents](../features/subagents.md).

## Watch

```bash
ana watch [path]   # requires a git repo; reviews each save in the background
```

See [Watch](../features/watch.md).

## CI review

```bash
ana ci "review this diff for correctness" --diff HEAD~1 --output-format json
```

Runs a one-shot review of a git diff — designed for CI pipelines. See
[Watch & CI review](../features/watch.md#ana-ci-one-shot-diff-review).

## Daemon / server

```bash
ana serve                  # start the backend in the foreground
ana daemon start           # same, managed with a PID file
ana daemon stop
ana daemon status
```

## Related

- [Interactive mode](interactive-mode.md) — slash commands and plan mode
- [Headless mode](headless.md) — scripting with `ana print`
- [Settings](../configuration/settings.md) — configuration precedence
