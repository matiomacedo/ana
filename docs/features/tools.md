# Tools

Ana registers **34 built-in tools**, plus any tools contributed by
connected [MCP servers](../extend/mcp.md) or enabled
[plugins](../extend/plugins.md).

Which tools are available in a session is controlled by the active
[permission mode](../configuration/permissions.md): `plan` mode gets a
fixed read-only allowlist; `default`/`auto_accept` get every registered
tool, with destructive ones gated by a confirmation prompt (skipped in
`auto_accept`). Permission rules can further allow/deny/ask per action on
top of that. Every file path is validated by the
[path-safety layer](../reference/security.md#path-safety), and every tool
result passes through secrets redaction and content isolation before the
model sees it.

| Tool | Destructive | Available in `plan` |
|------|-------------|----|
| `read_file` | No | Yes |
| `edit_file` | Yes | No |
| `edit_symbol` | Yes | No |
| `multi_edit` | Yes | No |
| `write_file` | Yes | No |
| `list_directory` | No | Yes |
| `code_search` | No | Yes |
| `graph_explain` | No | Yes |
| `graph_path` | No | Yes |
| `grep` | No | Yes |
| `glob` | No | Yes |
| `diff` | No | Yes |
| `git` | No | Yes |
| `web_search` | No | Yes |
| `webfetch` | No | Yes |
| `run_python` | No | No |
| `shell_command` | Yes | No |
| `run_shell_readonly` | No | Yes |
| `rename_file` | Yes | No |
| `delete_file` | Yes | No |
| `move_file` | Yes | No |
| `apply_patch` | Yes | No |
| `undo` | Yes | No |
| `lsp_definition` | No | Yes |
| `lsp_references` | No | Yes |
| `lsp_diagnostics` | No | Yes |
| `lsp_hover` | No | Yes |
| `lsp_symbols` | No | Yes |
| `lsp_rename` | Yes | No |
| `task` | No | No |
| `skill` | No | Yes |
| `todo` | No | Yes |
| `write_plan` | No | Yes |
| `expand_output` | No | Yes |

## File tools

**`read_file(path)`** — reads a file from disk.

**`write_file(path, content)`** — writes content to a file, creating parent
directories as needed. Destructive; confirms before executing (unless
`auto_accept`), then runs [post-edit verification](verification.md).

**`edit_file(path, old_string, new_string, replace_all?)`** — replaces an
exact text snippet in an existing file. Preferred over `write_file` for
modifying existing files. Destructive; same confirmation and verification
path as `write_file`.

**`edit_symbol(path, symbol, new_source)`** — replaces a whole function,
class, or method *by name* (`'my_func'`, `'MyClass.method'`) with new
source, no exact-text matching required — the reliable choice for small
local models rewriting a full definition. Python spans come from the AST
(decorators included); other languages use the running language server's
document symbols. Destructive.

**`multi_edit(path, edits)`** — applies several `edit_file`-style
search/replace edits to one file in a single atomic call: all edits succeed
or the file is left untouched, with the error naming the failing edit.
Destructive.

**`rename_file(path, new_path)` / `move_file(path, dest)` /
`delete_file(path)`** — filesystem mutations. All destructive.

**`list_directory(path)`** — lists files and directories at a path
(non-recursive).

**`glob(pattern)`** — finds files matching a glob pattern.

**`grep(pattern, include?)`** — searches for a regex pattern in files
within the project directory.

**`code_search(query, top_k?)`** — semantic search over the project's
[code index](memory.md#code-index-semantic-code-search): finds code by
meaning when exact identifiers aren't known. The index builds in the
background on first use.

**`graph_explain(symbol, file?)`** — explains one symbol from the
project's deterministic code graph: definition site, calls, callers, and
inheritance, each edge tagged `[EXTRACTED]` (explicit in source) or
`[INFERRED]` (name-resolved cross-file). The graph is built by tree-sitter
in the background — zero model calls.

**`graph_path(from_symbol, to_symbol?, max_results?)`** — with
`to_symbol`, the shortest connection between two symbols; without it, an
impact list of what depends on `from_symbol` (depth 2).

**`diff(path_a, path_b)`** (or `diff(path, snapshot_id)`) — a unified diff
between two file versions, or a file and one of its snapshots.

**`git(subcommand, args?)`** — read-only repository inspection: `status`,
`diff`, `log`, `show`, or `blame`. Arguments are passed as an argv list (no
shell) and flags are restricted to a safe read-only set, so it cannot
mutate the repo or smuggle options.

**`apply_patch(path, patch)`** — applies unified diff content to a file.
Destructive.

**`undo(path?)`** — restores the most recent snapshot for a file (or the
latest edited file). Destructive (it mutates the file back). See
[Sessions & rewind](../usage/sessions.md).

## Execution tools

**`run_python(code, timeout_secs?)`** — executes Python in a
RestrictedPython sandbox: no `subprocess`/`socket`/`os.system`, path-scoped
`open()`, output truncated at 8,000 characters, default 30s timeout.

**`shell_command(command, timeout_secs?)`** — runs a shell command through
the sandbox factory (Docker → Bubblewrap → local fallback, see
[Security](../reference/security.md#sandbox)). Destructive.

**`run_shell_readonly(command, timeout_secs?)`** — same sandbox,
restricted to read-only inspection commands; this is the shell available in
`plan` mode.

## Web tools

**`web_search(query)`** — searches the web via the configured provider
(`ANA_SEARCH_PROVIDER`: `duckduckgo` by default, or `tavily`/`brave` with
an API key).

**`webfetch(url)`** — fetches a URL's content, with SSRF guards on
redirects.

## LSP tools

**`lsp_definition` / `lsp_references` / `lsp_hover` / `lsp_diagnostics` /
`lsp_symbols`** — go-to-definition, find-references, hover info,
diagnostics, and document symbols, backed by a real language server:

| Language | Server |
|---|---|
| Python (`.py`) | `pyright-langserver` |
| TypeScript/JS (`.ts`, `.tsx`, `.js`, …) | `typescript-language-server` |
| Rust (`.rs`) | `rust-analyzer` |
| Go (`.go`) | `gopls` |

**`lsp_rename(file_path, line, character, new_name)`** — renames a symbol
project-wide via the language server and applies the returned edit,
snapshotting each touched file first. Aborts if any edit falls outside the
project. Destructive.

## Meta tools

**`task(description, subagent_type)`** — spawns a
[subagent](subagents.md) (a fresh invocation of the same graph, forced
into `plan` mode) to research or explore without polluting the parent's
context; only the final answer returns.

**`skill(name)`** — loads the full body of a named
[skill](../extend/skills.md) on demand.

**`todo(items)`** — maintains the model's own todo list for multi-step
tasks (the full list is passed on every call).

**`write_plan(content)`** — saves the model's implementation plan to
`<project>/.ana/plan.md`; the one write allowed in `plan` mode.

**`expand_output(handle)`** — retrieves the full text of a previous tool
output that was paged/truncated when returned.

## Related

- [Permission modes](../configuration/permissions.md) — how tool access is
  gated
- [Verification](verification.md) — what runs after a file-mutating tool
- [MCP servers](../extend/mcp.md) — adding external tools
