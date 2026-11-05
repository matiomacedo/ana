# Memory

Ana keeps the conversation inside the model's context window, and remembers
what stays true about a project. Within a session that means the message
window and its summaries. Across sessions, only three things carry over:
`ana.md`, per-project lessons, and an optional project brief. A new session
doesn't see earlier sessions' conversations or summaries.

## Project instructions (`ana.md`)

If the project has an `ana.md`, it goes into the system prompt on every turn,
labelled as project instructions. The first 8,000 characters are sent, and the
prompt says so if the file is cut. Edits apply from the next turn.

It loads whether or not you've [trusted the project](../reference/security.md):
it's text, and any tool call it asks for still goes through the permission
checks. Run `/init` to generate one. In a chat session with no `ana.md`, Ana drafts
one after your first turn finishes, so it never delays your first answer.

## The context window

The model sees the system prompt, then the message window: the conversation so
far, with older parts replaced by summaries. Before every model call, Ana
estimates the next prompt from the size of the last one plus what has been added
since. If that's over **75% of `num_ctx`**:

1. Large tool results from before the latest step are cut to their first 1,000
   characters. This needs no model call, and often it's enough.
2. If not, Ana compacts and waits for the result before calling the model, so a
   prompt doesn't outgrow the window while a summary is being written. You see
   "Compacting the conversation", and Esc interrupts it.

Compaction summarises the oldest messages and keeps the newest that fit:

- Your latest request stays word for word, whatever else is summarised.
- A tool call and its results are kept or summarised together.
- Earlier summaries stay as written rather than being summarised again. Once
  they pass 15% of the prompt budget the oldest are dropped from the window; the
  summary file keeps them.
- A summary that comes back empty, or no shorter than what it summarises, is
  refused and the conversation stays as it was.
- After a failure Ana waits a few steps before trying again, and waits longer
  each time.

If a prompt still doesn't fit, you get a warning saying so. Ollama cuts an
oversized prompt without telling you, so this is the only sign. Run `/compact`,
or use a model with a larger context.

`/compact` compacts now, keeping only the latest exchange. The fixed cost of the
prompt (system prompt, tool schemas, repo map) can't be compacted, so `/context`
never reaches zero.

`/context` shows two figures: `core` is the message window and `overhead` is
everything else, measured from the last call. The window itself is set as
described in [Context window](../configuration/models.md#context-window).

## Summaries

Each compaction adds to one file, `~/.ana/memory/<session-id>/summary.json`.
A session's window is restored from its checkpoint after a restart, so summaries
aren't fed back to the model. The file is there for you to read and search:

```bash
ana memory list                     # every session's summaries
ana memory search "parser"          # or /memory parser in chat
ana memory delete <session-id>
ana memory stats                    # per-session counts + LanceDB size
```

`/rewind` removes summaries written after the point you rewound to.

!!! note "Upgrading from an older version"
    Older versions kept vector tables and per-session git repos. Ana no longer
    uses them. They stay in `~/.ana/lancedb` and `~/.ana/memory` until you delete
    them. Old `compaction_*.json` files still show up in `ana memory list` and
    `search`, but `delete` and `prune` leave them alone, and they never reach the
    model.

## Retention policies

The configured policy (`ANA_MEMORY_RETENTION`, default `30_days`) is enforced by
a sweep at every backend startup, which deletes expired summaries and old events:

| Policy | Keeps summaries for |
|--------|-----------------|
| `session_end` | Deleted at the next sweep or prune |
| `1_day` | 1 day after creation |
| `30_days` | 30 days (default) |
| `1_year` | 1 year |
| `forever` | Never deleted |

```bash
ana memory prune --policy 30_days --yes    # apply a policy now
```

Change the default in `.env` (`ANA_MEMORY_RETENTION=1_year`) or
`~/.ana/cli_config.toml` (`retention_policy = "1_year"`).

## Code index (semantic code search)

Ana keeps a LanceDB-backed semantic index of the project's source: files are
chunked along AST boundaries and embedded, and refreshed incrementally by mtime
in the background, so indexing never blocks the conversation.

- A compact **repo map** (one line per file, ranked by import in-degree) is
  always in the system prompt. It's built once per session.
- The model searches the index with the `code_search` [tool](tools.md), which
  builds it on first use.
- `ANA_CODE_RAG=on` also adds search results to every turn. It's off by default.

A deterministic **code graph** (tree-sitter, zero model calls) powers the
`graph_explain` and `graph_path` tools and finds the tests an edit affects.
Imports resolve to files for Python (including relative imports and one level of
`__init__` re-exports), JavaScript and TypeScript, Java and Go. Rust, C# and PHP
imports are matched by path only, so most stay unresolved. Release builds include
the grammars; installed from source, each downloads on first use. If one is
missing Ana tells you which files were skipped.

### What gets indexed

The index covers the **session's project directory** and nothing outside it.
Symlinks that point elsewhere are not followed, so the directory `ana` was
started in is the boundary.

Beyond source code, it includes web and markup files, stylesheets, templates,
schemas and IDLs, infrastructure and config (`.yaml`, `.toml`, `.tf`, `.hcl`,
`.nix`), documentation (`.md`, `.rst`, `.adoc`), and extension-less build
files such as `Dockerfile`, `Makefile` and `Jenkinsfile`. Twenty-nine
languages have a tree-sitter grammar and chunk on their definitions;
everything else chunks on overlapping line windows, which is enough to search.

Deliberately excluded:

- **Hidden paths**, which is where credentials and tool caches live —
  `.env`, `.npmrc`, `.netrc`, `.ssh/`, `.aws/`. CI configuration is the
  exception and stays searchable: `.github/`, `.gitlab/`, `.circleci/`,
  `.pre-commit-config.yaml` and similar.
- **Lock files** (`package-lock.json`, `uv.lock`, `Cargo.lock`, `go.sum`, …)
  and generated directories (`node_modules`, `dist`, `build`).
- **Data JSON.** Only well-known config files (`package.json`,
  `tsconfig*.json`, `composer.json`, …) are read; everything else with a
  `.json` suffix is treated as data.

Discovery stops at 3,000 files. When that limit bites, grammar-backed source
is kept ahead of docs and config, so a large `docs/` tree cannot crowd out
the code.

!!! warning "Start `ana` inside the project you want indexed"
    The root is fixed when the session is created, from your working
    directory. Starting `ana` from your home directory points the index at
    your whole home directory — irrelevant results, and slow.

## Lessons (durable project knowledge)

When you leave `ana chat`, Ana distils durable, per-project facts from the
session in the background — conventions, build/test commands, architecture notes,
stated preferences — into a lessons store. `ana print` doesn't. This is distinct
from compaction summaries (which capture *what happened* in a session) and from
crystallized skills (which capture *reusable procedures*): lessons capture *facts
about the project* that should inform future sessions.

On each turn, up to two lessons are added to the context, and only those close
enough to your request to be relevant. Lessons need an embedding model and don't
expire.

## Sleep-time consolidation (experimental)

With `ANA_SLEEP_TIME=on`, an idle-time scheduler spends unused GPU time
turning raw memory into learned memory (all calls on the background-role
model, so the chat model stays loaded):

- **Lesson merge** — near-duplicate lessons collapse into one precise
  sentence each; when lessons contradict, the newer one wins. A merge that
  would grow or empty the list is rejected — consolidation can compress
  memory but never invent it.
- **Project brief** — each project's compaction summaries and lessons are
  distilled into a ~200-word brief, injected into the stable system-prompt
  prefix alongside the repo map (framed as reference, never instructions).

Runs at most once per project per day, only while no turn is in flight, and
never at all unless explicitly enabled.

## Related

- [Sessions & rewind](../usage/sessions.md) — what else persists per session
- [Architecture](../reference/architecture.md) — where memory sits in the
  agent graph
