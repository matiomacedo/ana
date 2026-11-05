# Sessions, rewind & undo

Every conversation is a **session**: a durable thread with its own
permission mode, project directory, conversation history, and memory.
Sessions survive backend restarts — by default the agent graph checkpoints every
step to SQLite, so a resumed session continues from the last step that finished,
even after a crash mid-turn. `ANA_CHECKPOINT_DURABILITY=exit` writes one checkpoint
per turn instead, which is faster but loses a turn that crashes.

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
snapshots taken before each write. Rewinding to before the first message empties
the conversation and restores every file the session edited.

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
| Compaction summaries | [`~/.ana/memory/<session-id>/summary.json`](../features/memory.md#summaries) | Yes |
| In-context conversation window | Rebuilt from checkpoints | Yes |

Delete a single session, along with its checkpoints, with
`ana session delete <id>`; wipe everything by
stopping the backend and removing `~/.ana/`
(see [Troubleshooting](../reference/troubleshooting.md#resetting-state)).

## Titles

A new chat session gets its title from your first message, generated after the first
turn finishes so it doesn't delay your first answer. If you send another message
before it's done, Ana stops it and tries again after that turn. An interrupted turn
skips it.

## Related

- [Memory](../features/memory.md) — what carries across sessions
- [Interactive mode](interactive-mode.md) — all slash commands
