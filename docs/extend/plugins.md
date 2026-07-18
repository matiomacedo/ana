# Plugins

Plugins are Python packages that hook into Ana's lifecycle — inspecting or
modifying behaviour at defined points rather than adding tools (use
[MCP](mcp.md) for that).

## Lifecycle hooks

A plugin subclasses the `AnaPlugin` base class and registers for events:

| Hook | Fires |
|---|---|
| `TOOL_EXECUTE_BEFORE` / `TOOL_EXECUTE_AFTER` | Around every tool call |
| `CHAT_MESSAGE` | On each user message |
| `SESSION_START` / `SESSION_END` | At session boundaries |
| `PERMISSION_EVALUATE` | When a permission decision is being made |

## Installing and managing

Plugins are discovered from `~/.ana/plugins/` and
`<project>/.ana/plugins/` (each plugin directory needs a `plugin.json`
manifest or an `__init__.py` exposing an `AnaPlugin` subclass), or via
Python entry points.

```bash
ana plugin list
ana plugin install <repo-url>     # git-clones and imports the repo
ana plugin enable|disable <name>
ana plugin remove <name>
```

`/plugin` in chat manages the same list without leaving the session.

!!! danger "Plugins are trusted code"
    Plugins are **not sandboxed** — `ana plugin install` git-clones a repo
    and imports it directly, running arbitrary Python at load time. Treat
    plugin sources the same as any other trusted dependency, not as
    untrusted input.

## Related

- [Security](../reference/security.md#extensibility-trust-boundaries)
- [Hooks & custom commands](hooks.md) — shell-level hooks that don't
  require writing Python
