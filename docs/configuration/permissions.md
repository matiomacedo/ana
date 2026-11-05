# Permission modes

Ana runs one agent with one system prompt. What varies between sessions is
**how much it may touch** — controlled by a permission mode, not a set of
distinct agent personalities.

Switch with ++shift+tab++ in chat (cycles `default` → `auto_accept` → `plan`),
`/mode <plan|default|auto_accept>`, `ana chat --mode ...`, or
`ana session new --mode ...`.

## `plan`

Read-only research. No file edits, no shell and no code execution. Tool allowlist:
`read_file`, `list_directory`, `glob`, `grep`, `diff`, `git`, `code_search`,
`graph_explain`, `graph_path`, `web_search`, `webfetch`, `skill`, `todo`, the LSP
tools (`lsp_definition`, `lsp_references`, `lsp_diagnostics`, `lsp_hover`,
`lsp_symbols`), `expand_output`, and any MCP or plugin tool marked read-only, plus
`write_plan`, whose only write is `<project>/.ana/plan.md`.

`webfetch` asks first here too, because a URL can carry out what the model has read.
Everything else in the list runs without asking. `git` is limited to `status`, `diff`,
`log`, `show` and `blame`.

```bash
ana chat --mode plan
# ❯ Plan how to migrate this Flask app to FastAPI
# ❯ What steps are needed to add OAuth2 to this project?
```

## `default`

All tools are available. Destructive tools (`write_file`, `edit_file`, `edit_symbol`,
`multi_edit`, `delete_file`, `rename_file`, `undo`, `shell_command`, `webfetch`,
`lsp_rename`, and MCP tools not marked read-only) pause with a preview until you
approve. This is the default for new sessions.

```bash
ana chat --mode default --project ~/myapp
# ❯ Add input validation to the signup endpoint
# ❯ Fix the failing test in test_auth.py
```

Answering **always** at a prompt stops confirmations for that tool for the rest of
the session. For `shell_command` it covers one program: `always` on `git status`
also covers `git log`, but `python -c ...` still asks. It's a broad answer for a
program like `python` or `node`, which can do anything.

## `auto_accept`

Same tool access as `default`, but the confirmation pause is skipped and destructive
tools run immediately. The [checks on tool calls](../reference/security.md#checks-on-tool-calls)
and `deny` and `ask` rules still apply.

```bash
ana chat --mode auto_accept --project ~/myapp
```

!!! warning
    Use this only in a disposable environment or when you've reviewed the
    plan already — it removes the last human checkpoint before a write,
    delete, or shell command executes.

## Permission rules

Independent of mode, `~/.ana/permissions.db` holds wildcard rules with the effect
`allow`, `deny` or `ask`. A rule can deny an action or force a confirmation the mode
wouldn't otherwise ask for. `allow` can't skip a destructive tool's confirmation.

Each call produces one or more targets, and the strictest answer wins. A call that
matches no rule is allowed.

| Action | Tools | Target |
|---|---|---|
| `read` | `read_file`, `list_directory`, `grep`, `glob`, `diff`, the read-only LSP tools | The path |
| `read` | `git` | Each path or ref argument, so `HEAD:.env` counts as `.env` |
| `read` | `shell_command` | Each non-flag argument, and the value of `--flag=value` |
| `read`, `write` | `rename_file` | Read and write on the source, write on the destination |
| `write` | `write_file` | The path |
| `edit` | `edit_file`, `edit_symbol`, `multi_edit`, `lsp_rename`, `undo` | The path |
| `delete` | `delete_file` | The path |
| `search` | `grep`, `glob` | The pattern |
| `search` | `code_search`, `graph_explain`, `graph_path` | The query or symbol |
| `bash` | `shell_command` | The whole command |
| `network` | `web_search`, `webfetch` | The query or URL |
| `execute` | `skill` | The skill name |
| `execute` | MCP and plugin tools, `task`, `todo`, `write_plan`, `expand_output`, `git` with no arguments | The tool name |

Path targets resolve against the project and through symlinks before matching. A
relative pattern starts at the project root. `*` matches across `/`, and matching
ignores case for `deny` and `ask` but not `allow`.

Seeded defaults: deny `read` on `**/.env*`, in any directory; allow `bash` on
`npm run *`, `npm test`, `git status` and `git log *`. Remove the rule with
`ana permissions remove` if you need those files read.

A file named exactly `.env.example` is exempt, so the model can read it. `.env.local`,
`.envrc` and `.env.example.local` stay denied, and so does a `.env.example` symlink
that points at a secret. To block it too, add a deny rule for `**/.env.example`.

If you remove every rule, including the defaults, every tool call asks. Run
`ana permissions seed` to restore them.

!!! note "`ask` rules fire in every mode"
    An `ask` rule pauses for confirmation in **every** mode, including `auto_accept`
    and headless `ana print`, where the run then fails. Reserve it for genuinely
    sensitive patterns.

```bash
ana permissions list
ana permissions add bash "docker *" allow --desc "Allow docker commands"
ana permissions add edit "*.env" ask --desc "Confirm edits to env files"
ana permissions add execute "mcp_*" deny --desc "No MCP tools"
ana permissions remove <rule-id>
ana permissions clear
ana permissions seed   # re-seed the built-in defaults
```

Rules can also be managed in-chat with `/permissions`.

## Switching modes mid-session

Press ++shift+tab++ at the prompt to cycle `default` → `auto_accept` → `plan`.
The input box repaints with the new mode and keeps whatever you have typed, so
you can change your mind about a request before sending it.

```bash
# In chat:
/mode auto_accept

# Via the API:
PATCH /sessions/{id}/mode  {"mode": "auto_accept"}
```

Cycling into `plan` records the mode you came from, so `/plan off` restores it
exactly as it would after `/plan`.

## How a tool call is authorized

Every tool call passes through the same gate, in order:

1. **Mode allowlist.** Is the tool available in this mode at all?
2. **Safety checks.** [Destructive commands and credential paths](../reference/security.md#checks-on-tool-calls)
   are blocked outright, in every mode.
3. **Confirmation.** A destructive tool pauses for you, unless the mode is
   `auto_accept` or you answered **always**.
4. **Permission rules.** A `deny` stops the call. An `ask` pauses for you, unless step 3
   already did.
5. **Hooks and plugins.** Global ones, and the project's own if it's
   [trusted](../reference/security.md#project-trust). A `before` hook can block the call.
6. **Path safety.** File tools check the path as they run. See
   [path safety](../reference/security.md#path-safety).

Several read-only calls in one model response run in parallel only if every one of
them clears steps 1, 2 and 4 without asking. Otherwise only the first runs, and the
model is told to re-issue the rest.

## Related

- [Tools](../features/tools.md) — the full registry with per-mode availability
- [Security](../reference/security.md) — the layers underneath permissions
