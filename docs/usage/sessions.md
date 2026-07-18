# Sessions, rewind & undo

Every conversation is a **session**: a durable thread with its own
permission mode, project directory, conversation history, and memory.
Sessions survive backend restarts — the agent graph checkpoints every step
to SQLite, so a resumed session continues exactly where it stopped.

## Managing sessions

```bash
ana session list
ana session new --mode plan --project ~/myproject
ana session resume a3f1                # ID prefix works
ana session delete a3f1bc7d-...
```

Inside a chat:

| Command | Action |
|---|---|
| `/session` | Show the current session |
| `/sessions` | List all sessions |
| `/resume [id]` | Switch to another session (no arg → picker) |
| `/fork` | Fork this session and continue on the copy |
| `/export [path]` | Export this session to a JSON file |

`/fork` copies the full conversation state into a new session — useful for
trying a risky direction while keeping the original intact.

## Rewind

`/rewind [turns]` rolls the session back N user turns — **conversation and
workspace together**. It forks the session's checkpoint thread back to that
point and restores every file the agent edited since, from the per-file
snapshots taken before each write.

```
❯ /rewind 2
Rewound 2 turns. 3 files restored to their pre-edit snapshots.
```

`/undo` is shorthand for a one-turn rewind with a confirmation prompt.

## The `undo` tool

Separate from `/rewind`, the model itself can call the `undo` tool
mid-session to restore the most recent snapshot of a single file — its own
escape hatch when an edit goes wrong. See
[Tools](../features/tools.md#file-tools).

## What persists where

| State | Lives in | Survives restart? |
|---|---|---|
| Conversation + graph state | `~/.ana/checkpoints/checkpoints.db` | Yes |
| Session metadata (mode, project, title) | `~/.ana/sessions.db` | Yes |
| Pre-edit file snapshots | snapshot store per project | Yes |
| Compaction summaries | [Tier 2/3 memory](../features/memory.md) | Yes |
| In-context conversation window | Tier 1 (rebuilt from checkpoints) | Yes |

Delete a single session with `ana session delete <id>`; wipe everything by
stopping the backend and removing `~/.ana/`
(see [Troubleshooting](../reference/troubleshooting.md#resetting-state)).

## Related

- [Memory](../features/memory.md) — what carries across sessions
- [Interactive mode](interactive-mode.md) — all slash commands
