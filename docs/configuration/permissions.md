# Permission modes

Ana runs one agent with one system prompt. What varies between sessions is
**how much it may touch** — controlled by a permission mode, not a set of
distinct agent personalities.

Switch with `/mode <plan|default|auto_accept>` in chat,
`ana chat --mode ...`, or `ana session new --mode ...`.

## `plan`

Read-only research. No writes, no code execution, no state-changing shell
commands. Tool allowlist: `read_file`, `list_directory`, `glob`, `grep`,
`diff`, `git`, `code_search`, `graph_explain`, `graph_path`, `web_search`,
`webfetch`, `run_shell_readonly`, `skill`, `todo`, the LSP tools
(`lsp_definition`, `lsp_references`, `lsp_diagnostics`, `lsp_hover`,
`lsp_symbols`), `expand_output` — plus `write_plan`, the one write allowed:
saving the plan to `<project>/.ana/plan.md`.

```bash
ana chat --mode plan
# ❯ Plan how to migrate this Flask app to FastAPI
# ❯ What steps are needed to add OAuth2 to this project?
```

## `default`

All tools are available. Destructive tools (`write_file`, `edit_file`,
`delete_file`, `rename_file`, `move_file`, `apply_patch`, `undo`,
`shell_command`, `lsp_rename`, and any model-flagged destructive action)
pause with a diff preview until you approve. This is the default for new
sessions.

```bash
ana chat --mode default --project ~/myapp
# ❯ Add input validation to the signup endpoint
# ❯ Fix the failing test in test_auth.py
```

Answering **Always** at a prompt stops confirmations for that tool for the
rest of the session.

## `auto_accept`

Same tool access as `default`, but the confirmation pause is skipped —
destructive tools run immediately. `deny`/`ask` permission rules (below)
still apply regardless of mode.

```bash
ana chat --mode auto_accept --project ~/myapp
```

!!! warning
    Use this only in a disposable environment or when you've reviewed the
    plan already — it removes the last human checkpoint before a write,
    delete, or shell command executes.

## Permission rules (allow/deny/ask)

Independent of mode, a persistent rule store (`~/.ana/permissions.db`)
holds wildcard rules per action type (`bash`, `read`, `write`, `edit`,
`delete`, `execute`, `search`, `network`) with effect `allow`, `deny`, or
`ask`. Rules are evaluated **on top of** the mode's tool allowlist — a rule
can deny or force confirmation on an action the mode would otherwise allow.

Seeded defaults: allow `npm run *`, `npm test`, `git status`, `git log *`;
deny `rm -rf *` and reads of `./.env*`.

!!! note "`ask` rules fire in every mode"
    An `ask` rule pauses for confirmation in **every** mode — including
    `auto_accept` and headless `ana print` — so reserve `ask` for genuinely
    sensitive patterns.

```bash
ana permissions list
ana permissions add bash "docker *" allow --desc "Allow docker commands"
ana permissions add edit "*.env" ask --desc "Confirm edits to env files"
ana permissions remove <rule-id>
ana permissions clear
ana permissions seed   # re-seed the built-in defaults
```

Rules can also be managed in-chat with `/permissions`.

## Switching modes mid-session

```bash
# In chat:
/mode auto_accept

# Via the API:
PATCH /sessions/{id}/mode  {"mode": "auto_accept"}
```

## How a tool call is authorized

Every tool call passes through the same gate, in order:

1. **Mode allowlist** — is the tool available in this mode at all?
2. **Permission rules** — does an `allow`/`deny`/`ask` rule match the
   action and target?
3. **Confirmation** — destructive tool in `default` mode (or an `ask` rule
   anywhere): pause with a preview until you decide.
4. **Path safety** — file paths must resolve inside the project directory
   and clear the [path-safety checks](../reference/security.md#path-safety).

## Related

- [Tools](../features/tools.md) — the full registry with per-mode availability
- [Security](../reference/security.md) — the layers underneath permissions
