# Interactive mode

`ana` (or `ana chat`) opens an interactive session with streaming replies, a
status bar showing the model and context budget, and a set of slash commands
that work without leaving the chat.

## Slash commands

| Command | Action |
|---------|--------|
| `/help [command]` | Show commands, or what one does (a short terminal lists names only) |
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

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| ++shift+tab++ | Cycle permission mode: `default` → `auto_accept` → `plan` |
| ++tab++ | Complete slash commands, their arguments, and `@` file mentions |
| ++esc++ | Interrupt the current turn |
| ++ctrl+c++ | Interrupt the current turn; at an empty prompt, exit chat |

++shift+tab++ switches mode without leaving the prompt. The box repaints with
the new mode's name and colour, and anything already typed is kept. On screen
`default` reads **Ask first**, `auto_accept` reads **Auto**, and `plan` reads
**Plan**; commands and flags keep taking the lowercase names.

```
╭─ ❮ Ask first ❯ · qwen3.5:4b ────────────────╮
│ ❯ fix the header

    [shift+tab]

╭─ ❮ Auto ❯ · qwen3.5:4b ─────────────────────╮
│ ❯ fix the header
```

## Mentioning files with `@`

Type `@` to insert a path from the current project. Completion is fuzzy, so
`@archmd` finds `docs/architecture.md`; folders complete too, and mentions are
ranked by how recently and often you have used them.

The list is scoped to the **session's project directory** — the directory
`ana` was started in — and never reaches outside it. Inside a git repository
it follows `git ls-files`, so ignored files stay out; elsewhere it walks the
directory, skipping hidden and generated paths.

!!! tip "Start `ana` inside your project"
    A session's root is fixed when it is created, from your working
    directory. Starting `ana` from your home directory scopes `@` — and the
    agent's file tools and code index — to your whole home directory. Ana
    prints a warning when it detects this.

## Interrupting a turn

Press ++esc++ while the agent is working — mid-answer, before a tool runs, or
while the model is still loading — and the turn stops immediately:

```
│ ❯ refactor the auth module
╰──────────────────────────────────────────╯
● Read auth.py   241 lines
⠧ Waiting for model…  7s   turn 12s   esc to stop

⎿  Interrupted by user
```

Whatever the agent produced before the interrupt stays in the conversation,
followed by a `[Request interrupted by user]` marker, so your next message
continues from where things really stopped and the model can see that its work
was cut short. The model stops generating straight away, so the next message
isn't queued behind an answer you abandoned.

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

```
Run this command?
  ls -la
[y]es  [n]o  [a]lways for ls  (n) a
Won't ask again for ls in this session.
● Ran ls -la   9 lines
```

- **`y`** — run this one call
- **`a`** — run it and stop asking for this tool, or for this program in the
  shell, for the rest of the session
- **`n`** or Enter — reject; the model sees the rejection and adjusts

**Always** persists for the whole session, including when the call you
approved then fails. The preview simulates the edit before you decide, so it
also tells you when an edit *cannot* apply — a stale `old_string`, or a change
that would leave the file untouched — rather than showing you a blank panel to
approve.

Once a tool is running without prompts — after **Always**, or in
`auto_accept` — Ana prints the diff of each edit as it is applied, so changes
are still visible when nothing is asking for approval:

```
╭─ Edited calc.py   +1 -1 ─────────────────────╮
│ --- a/calc.py                                │
│ +++ b/calc.py                                │
│ @@ -1,2 +1,2 @@                              │
│  def f():                                    │
│ -    return 1                                │
│ +    return 1  # note.                       │
╰──────────────────────────────────────────────╯
```

Each tool call gets one line, `●` when it worked and `✗` when it didn't. Only
diffs and failures with more to say get a panel. The turn's last line says how it
went, and it doesn't call a turn done while the tests it checked still fail:

```
! Finished with 1 failing test: test_calc.py   30s
```

The first finished turn in a project without an `ana.md` also says it's writing one.

`auto_accept` mode skips the prompts entirely; `deny`/`ask`
[permission rules](../configuration/permissions.md#permission-rules)
still apply in every mode.

## The status bar

The chat status bar shows the active model, permission mode, and a context
gauge (percentage of the model's context window in use). When the
conversation approaches the limit, Ana
[compacts automatically](../features/memory.md#compaction) in the
background; `/compact` forces a more aggressive pass on demand, and
`/context` breaks down exactly where the tokens are going — plus the window
Ana loaded the model with and what chose it:

```
╭────────────── Context · 46% (12,000/26,214 tokens) ──────────────╮
│ core                       ██████████░░░░░░░░░░  7,000/13,107    │
│ recall                     █░░░░░░░░░░░░░░░░░░░  300/5,242       │
│ overhead (prompt + tools)  ███░░░░░░░░░░░░░░░░░  4,700 tokens    │
╰──────────────────────────────────────────────────────────────────╯
window: 32,768 (OLLAMA_CONTEXT_LENGTH) · model max 262,144
```

See [Context window](../configuration/models.md#context-window) for how that
window is chosen and how to change it.

## Skills in chat

Type `/skill <name>` (or bare `/skill` for a picker) to force a skill for
the next message. Custom slash commands you define as markdown files appear
alongside the built-ins — see
[Hooks & custom commands](../extend/hooks.md#custom-slash-commands).

## Related

- [Sessions & rewind](sessions.md) — resume, fork, rewind, undo
- [CLI reference](cli-reference.md) — everything outside the chat
