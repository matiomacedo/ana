# Interactive mode

`ana` (or `ana chat`) opens an interactive session with streaming replies, a
status bar showing the model and context budget, and a set of slash commands
that work without leaving the chat.

## Slash commands

| Command | Action |
|---------|--------|
| `/help` | Show command list |
| `/mode [plan\|default\|auto_accept]` | Switch permission mode (no arg → picker) |
| `/model [name]` | Switch model (no arg → picker) |
| `/plan` / `/plan off` / `/plan execute` | Enter plan mode / approve the plan / execute it |
| `/session` | Show current session |
| `/sessions` | List all sessions |
| `/models` | List available models |
| `/skills` | List pending (crystallized) skills |
| `/permissions [add\|remove …]` | View or edit permission rules |
| `/mcp [add\|remove …]` | List MCP servers and status; add/remove entries |
| `/plugin [enable\|disable\|install\|remove …]` | List and manage plugins |
| `/agents` | List background agents |
| `/hooks` | List configured tool/turn hooks |
| `/settings [key value]` | View and edit CLI + backend settings |
| `/stats` | Show this session's token and usage stats |
| `/skill [name]` | Use a skill for the next message (no arg → picker) |
| `/rewind [turns]` | Roll back the session N user turns |
| `/undo` | Undo the last turn (rewind 1, with confirmation) |
| `/compact` | Force an aggressive context compaction now |
| `/context` | Show the context budget breakdown |
| `/memory <query>` | Search memories from past sessions |
| `/init` | Generate/refresh the project's `ana.md` context file |
| `/review [focus]` | Review the uncommitted diff in this session |
| `/clear` | Clear the screen |
| `/resume [id]` | Switch to another session (no arg → picker) |
| `/fork` | Fork this session and continue on the copy |
| `/copy` | Copy the last reply to the clipboard |
| `/export [path]` | Export this session to a JSON file |
| `/exit`, `/quit`, `/q` | Leave the chat |
| ++ctrl+c++ | Cancel the current turn / exit chat |

## Plan mode

`/plan` switches the session to the read-only plan mode. When you ask for
implementation work there, the agent researches the codebase and saves its
plan to `<project>/.ana/plan.md` using the `write_plan` tool — the only
write allowed in plan mode.

- `/plan off` offers to approve and execute the plan: it restores your
  previous mode and instructs the agent to work through the plan.
- `/plan execute` does the same without the prompt.

```
❯ /plan
Plan mode on — read-only research. /plan off to leave.
❯ Plan how to add OAuth2 login to this app
… (agent reads code, writes .ana/plan.md) …
❯ /plan execute
```

See [Permission modes](../configuration/permissions.md) for what each mode
allows.

## Confirmation prompts

In `default` mode, destructive tools (file writes, deletes, shell commands)
pause the turn with a preview — a unified diff for edits, the exact command
for shell — and wait for your decision:

- **Yes** — run this one call
- **Always** — run it and stop asking for this tool for the rest of the session
- **No** — reject; the model sees the rejection and adjusts

`auto_accept` mode skips these prompts entirely; `deny`/`ask`
[permission rules](../configuration/permissions.md#permission-rules-allowdenyask)
still apply in every mode.

## The status bar

The chat status bar shows the active model, permission mode, and a context
gauge (percentage of the model's context window in use). When the
conversation approaches the limit, Ana
[compacts automatically](../features/memory.md#compaction) in the
background; `/compact` forces a more aggressive pass on demand, and
`/context` breaks down exactly where the tokens are going.

## Skills in chat

Type `/skill <name>` (or bare `/skill` for a picker) to force a skill for
the next message. Custom slash commands you define as markdown files appear
alongside the built-ins — see
[Hooks & custom commands](../extend/hooks.md#custom-slash-commands).

## Related

- [Sessions & rewind](sessions.md) — resume, fork, rewind, undo
- [CLI reference](cli-reference.md) — everything outside the chat
