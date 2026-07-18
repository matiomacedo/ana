# Skills

Skills are markdown instructions the agent can load when a task calls for
them — a lightweight way to teach Ana procedures without touching code.
There are two independent systems: **user-authored** skills you write, and
**auto-crystallized** skills Ana proposes from its own successful sessions.

## Built-in skills

Ana ships with: `solid`, `commit-message`, `code-review`,
`debug-systematically`, `write-tests`, `refactor-safely`,
`explain-codebase`.

## User-authored skills

A skill is a markdown file (`*.md`, or `<name>/SKILL.md`) with YAML
frontmatter, placed in `~/.ana/skills/` (global) or
`<project>/.ana/skills/` (project):

```markdown
---
name: my-skill
description: One-line trigger description shown in every system prompt.
allowed-tools: [read_file, grep]   # optional
---

Full skill body, loaded on demand via the `skill` tool or auto-injected
when the description overlaps the user's request.
```

**Shadowing:** by name, project skills shadow global ones, which shadow
built-ins.

**How skills activate.** A compact name+description index is injected into
every system prompt; matching skill bodies are then:

- **auto-loaded** when the description overlaps the user's request
  (token-overlap scoring),
- fetched **on demand** by the model via the `skill` tool, or
- **forced for one turn** by you with `/skill <name>` in chat.

## Auto-crystallized skills

Ana periodically inspects successful turns for a reusable procedure,
proposes it via a local model call, and stores it **pending**. Nothing is
trusted until a human approves it:

```bash
ana skills list             # pending crystallized skills
ana skills approve <id>     # materialises it as markdown under ~/.ana/skills/
ana skills reject <id>
ana skills export / import
```

Once approved, a crystallized skill is an ordinary markdown skill you can
read and edit like any other.

## Writing a good skill

- Keep the `description` specific — it's the trigger. "Review database
  migration files for reversibility" beats "database help".
- The body is instructions to the model, not documentation: imperative
  steps, concrete commands, what good output looks like.
- Use `allowed-tools` to scope a skill that should only ever read.

## Related

- [Interactive mode](../usage/interactive-mode.md) — `/skill` in chat
- [Hooks & custom commands](hooks.md) — custom slash commands (prompt
  templates), a related but simpler mechanism
