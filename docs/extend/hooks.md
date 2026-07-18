# Hooks & custom commands

Two lightweight extension points that need no Python: **shell hooks** run
around tool execution, and **custom slash commands** are prompt templates
you invoke by name.

## Shell hooks

Hooks are defined in `~/.ana/hooks.toml` (global) or
`<project>/.ana/hooks.toml` (project):

```toml
[[hooks]]
event = "before"          # "before" | "after" | "turn-end"
tools = ["write_file", "edit_file"]
command = "my-lint-gate"  # non-zero exit blocks the tool call (before only)
```

| Event | Fires | Special behaviour |
|---|---|---|
| `before` | Before the listed tools execute | Non-zero exit **blocks** the tool call |
| `after` | After the listed tools execute | — |
| `turn-end` | Once after each completed turn | e.g. auto-format the touched files |

List active hooks with `/hooks` in chat.

**Example — block edits when the tree has merge conflicts:**

```toml
[[hooks]]
event = "before"
tools = ["edit_file", "write_file", "apply_patch"]
command = "sh -c '! git ls-files -u | grep -q .'"
```

**Example — auto-format after every turn:**

```toml
[[hooks]]
event = "turn-end"
command = "ruff format ."
```

## Custom slash commands

Add your own commands as markdown files in `~/.ana/commands/` (global) or
`<project>/.ana/commands/` (project; shadows global by name). The file name
becomes the command; the body is a prompt template sent as a message, with
`$ARGUMENTS` replaced by whatever you type after the command:

```markdown
---
description: Summarise the current diff
arg-hint: "[focus]"
---
Run git diff and summarise the changes. $ARGUMENTS
```

Saved as `~/.ana/commands/diffsum.md`, this becomes `/diffsum` in every
chat:

```
❯ /diffsum focus on the API changes
```

Custom commands appear in `/help` alongside the built-ins.

## Which extension point do I want?

| I want to… | Use |
|---|---|
| Run a shell command around tool calls / turns | **Shell hooks** |
| Reuse a prompt I type often | **Custom slash command** |
| Teach the agent a procedure it applies on its own | [Skill](skills.md) |
| Add new tools | [MCP server](mcp.md) |
| Intercept Ana's internals in Python | [Plugin](plugins.md) |

## Related

- [Skills](skills.md)
- [Interactive mode](../usage/interactive-mode.md)
