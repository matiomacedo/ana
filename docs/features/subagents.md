# Subagents & background agents

Ana has two independent mechanisms for work that shouldn't run in your main
conversation: **in-context subagents** (the `task` tool) and
**background agents** (`ana agents`).

## Subagents — the `task` tool

The model can spawn a subagent mid-turn via the `task` tool: a fresh
invocation of the **same agent graph** under a new thread ID, forced into
`plan` permission mode with a type-specific read-only allowlist:

| Subagent type | Tools |
|---|---|
| `explore` | read + search + LSP tools |
| `research` | the same, plus `web_search` / `webfetch` |

The subagent has no `task` tool of its own (a depth-1 recursion guard) and
runs to completion (max 10 iterations). Only its **final answer** — not its
intermediate tool calls — is returned to the parent session, keeping the
parent's context clean.

```
❯ How is caching handled across this monorepo?
  (agent spawns an explore subagent; dozens of file reads happen in the
   subagent's context; one summary comes back)
```

Because subagents are always in `plan` mode, they can never modify files or
run destructive commands, regardless of the parent session's mode.

## Background agents — `ana agents`

Background agents are **long-running sessions** driven in the background by
the backend's daemon component: it opens a normal session, sends it your
task, and polls it to completion (up to 1 hour), recording the final
result. State persists to `~/.ana/daemon/state.json`, so results survive
CLI restarts.

```bash
ana agents run "upgrade all deprecated API calls in src/ and run the tests"
ana agents list                            # running/finished agents
ana agents logs <id>                       # tail an agent's events
```

In chat, `/agents` lists them without leaving the session.

Use background agents for work that takes minutes and doesn't need your
supervision — they run under the same permission machinery as any session,
so destructive-action confirmation behaves according to the mode the agent
session was created with.

## The project-init agent

`/init` in chat (or the first run in a new project) launches a small
dedicated agent that surveys the project and generates `ana.md` — a
project-context file (conventions, structure, commands) injected into
future sessions. Re-run `/init` any time to refresh it.

## Related

- [Permission modes](../configuration/permissions.md) — why subagents are
  read-only
- [CLI reference](../usage/cli-reference.md#background-agents)
