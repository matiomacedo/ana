# Memory

Ana uses a three-tier memory system to maintain context across turns and
sessions, plus a semantic code index and a durable per-project lessons
store.

## The three tiers

```
Tier 1 — Core Context Window
  Always in context. The live conversation.
  When 90% full → compaction triggered.

Tier 2 — Recall Store (per session, in-memory)
  BM25 (40%) + vector (60%) hybrid retrieval.
  Stores compaction summaries.
  Rebuilt from Tier 3 on backend restart.

Tier 3 — Archival Store (persistent)
  LanceDB vector database + git-backed JSON files.
  Survives backend restarts.
  Source of truth for Tier 2 warmup.
```

### Token budget allocation

Ana allocates the model's effective context (80% of the advertised limit)
across four tiers:

| Tier | Budget | Contents |
|------|--------|----------|
| Core | 50% | System prompt + conversation history |
| Recall | 20% | Retrieved summaries from Tier 2 |
| RAG | 20% | Archival snippets from Tier 3 |
| Overhead | 10% | Tool definitions, mode suffix |

Check the live breakdown any time with `/context` in chat.

## Compaction

When the core tier reaches 90% of its budget:

1. The oldest 50% of conversation turns are summarised by the LLM
2. The summary is written to **both** Tier 2 and Tier 3
3. The summarised turns are replaced by a `[Memory compaction]` message
4. A compaction event is broadcast to connected clients

Compaction runs as a **background task**, so the conversation is never
blocked, and a begin/end guard ensures only one compaction is in flight per
session.

A user-initiated `/compact` is more aggressive than the automatic
threshold: it summarises everything except the trailing exchange, since you
explicitly asked for maximum recovery. The fixed prompt overhead (system
prompt, tool schemas, repo map) cannot be compacted — `/context` never
drops to zero.

## Memory retrieval

Once per user turn (before the first model call), Ana queries concurrently:

- Tier 2 (in-memory) for this session's compaction summaries
- Tier 3 (LanceDB) for archival context from older sessions — only when
  Tier 2 finds nothing
- The per-project lessons store and the semantic code index (when a
  project directory is set)

Retrieved context is injected as a clearly-labelled `<context>` block right
after the latest user message — **not** into the system prompt — so the
KV-cache prefix over the prior conversation survives across turns, and the
model is told the material is background reference, not instructions.

## Retention policies

The configured policy (`ANA_MEMORY_RETENTION`, default `30_days`) is
enforced automatically by a sweep at every backend startup — expired
archival summaries, their git-backed mirrors, and old events are deleted
without a manual prune:

| Policy | Keeps memory for |
|--------|-----------------|
| `session_end` | Deleted when the session ends |
| `1_day` | 1 day after creation |
| `30_days` | 30 days (default) |
| `1_year` | 1 year |
| `forever` | Never deleted |

```bash
ana memory prune --policy 30_days --yes    # apply a policy now
ana memory stats                            # per-session archival counts + DB size
```

Change the default in `.env` (`ANA_MEMORY_RETENTION=1_year`) or
`~/.ana/cli_config.toml` (`retention_policy = "1_year"`).

## Code index (semantic code search)

Separate from the conversational tiers, Ana maintains a LanceDB-backed
semantic index of the project's source: files are chunked along AST
boundaries and embedded, refreshed incrementally by mtime as a background
task each turn, so indexing never blocks the conversation.

- A compact **repo map** (one line per file, ranked by import in-degree) is
  always injected into the stable system-prompt prefix.
- The fuller semantic RAG lookup is controlled by `ANA_CODE_RAG` (`on` by
  default), and the model can query the index on demand via the
  `code_search` [tool](tools.md).

A deterministic **code graph** (tree-sitter, zero model calls) additionally
powers the `graph_explain` and `graph_path` tools for call/caller/
inheritance questions.

## Lessons (durable project knowledge)

Ana distils durable, per-project facts from sessions — conventions,
build/test commands, architecture notes, stated preferences — into a
lessons store. This is distinct from compaction summaries (which capture
*what happened* in a session) and from crystallized skills (which capture
*reusable procedures*): lessons capture *facts about the project* that
should inform every future session.

Search everything remembered about past work with `/memory <query>` in
chat.

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
